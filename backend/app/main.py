

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from google.cloud import storage, speech
from pathlib import Path
from datetime import timedelta
import os
import subprocess
import shutil
from pydantic import BaseModel
import requests
import json

app = FastAPI()


from dotenv import load_dotenv

load_dotenv()

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = os.getenv("BUCKET_NAME")
DGRAPH_GRAPHQL_ENDPOINT = os.getenv("DGRAPH_GRAPHQL_ENDPOINT")
MODUS_GRAPHQL_ENDPOINT = os.getenv("MODUS_ENDPOINT")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")







class PhraseQuery(BaseModel):
    phrase: str
    sport: str






storage_client = storage.Client()
speech_client = speech.SpeechClient()
bucket = storage_client.bucket(BUCKET_NAME)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)





def ai_normalize_with_modus(raw_text: str):
    """
    Normalize sports commentary using Modus AI.
    Sends a POST request to the Modus API with the transcription text as payload.

    Args:
        raw_text (str): The raw sports commentary to normalize.

    Returns:
        list: A list of normalized terms extracted from the commentary.

    Raises:
        Exception: If the request to the Modus API fails or the response is invalid.
    """
    try:
   
        graphql_query = {
            'query': '''
            query($rawText: String!) {
                normalizeSportsCommentary(rawText: $rawText)
            }
            ''',
            'variables': {
                'rawText': raw_text
            }
        }

      
        response = requests.post(MODUS_GRAPHQL_ENDPOINT, json=graphql_query)
        response.raise_for_status()  

    
        result = response.json()

   
        normalized_text = result.get('data', {}).get('normalizeSportsCommentary', '')
        return normalized_text.strip("[]").replace('"', '').split(", ")
    
    except requests.RequestException as e:
        raise Exception(f"HTTP request to Modus API failed: {e}")
    except Exception as e:
        raise Exception(f"AI normalization failed: {e}")




def normalize_transcription(raw_text: str) -> list:
    """
    Normalize raw transcription text into predefined soccer-specific terms.
    """
    normalized_terms = []
    for phrase, normalized in NORMALIZATION_MAP.items():
        if phrase in raw_text.lower():
            normalized_terms.append(normalized)
    return list(set(normalized_terms)) 

@app.get("/")
def read_root():
    return {"message": "Welcome to the Sports Commentary API"}


@app.post("/upload-to-gcs")
async def upload_to_gcs(file: UploadFile = File(...)):
    try:
    
        local_path = Path(UPLOAD_DIR) / file.filename
        with open(local_path, "wb") as f:
            f.write(await file.read())

        # Upload to Google Cloud Storage
        blob = bucket.blob(file.filename)
        blob.upload_from_filename(str(local_path))

      
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=24),
            method="GET",
        )


        os.remove(local_path)

        return {"message": "File uploaded successfully", "file_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")


@app.post("/extract-audio")
async def extract_audio(file: UploadFile = File(...)):
    try:
 
        input_path = Path(UPLOAD_DIR) / file.filename
        output_path = input_path.with_suffix(".mp3")  

        with open(input_path, "wb") as f:
            f.write(await file.read())

   
        video_blob = bucket.blob(file.filename)
        video_blob.upload_from_filename(str(input_path))
        video_url = video_blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=24),
            method="GET",
        )

        command = [
            "ffmpeg", "-i", str(input_path),
            "-q:a", "0", "-map", "a",
            str(output_path)
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        audio_blob = bucket.blob(output_path.name)
        audio_blob.upload_from_filename(str(output_path))
        audio_url = audio_blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=24),
            method="GET",
        )

      
        os.remove(input_path)
        os.remove(output_path)

        return {
            "message": "Audio extracted and uploaded successfully",
            "original_video_url": video_url,
            "audio_file_url": audio_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract audio: {e}")


@app.post("/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Process a video file by extracting audio, transcribing it, normalizing transcription,
    querying metadata, generating subtitles, and applying video overlay.
    """
    try:
  
        original_video_path = Path(UPLOAD_DIR) / file.filename
        with open(original_video_path, "wb") as f:
            f.write(await file.read())

  
        audio_path = original_video_path.with_suffix(".mp3")
        ffmpeg_command = [
            "ffmpeg", "-i", str(original_video_path),
            "-q:a", "0", "-map", "a",
            str(audio_path)
        ]
        subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

 
        with open(audio_path, "rb") as f:
            content = f.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            language_code="en-US",  
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True 
        )

        transcription_response = speech_client.recognize(config=config, audio=audio)
        
       
        transcription = []
        for result in transcription_response.results:
            alternative = result.alternatives[0]
            for word_info in alternative.words:
                start_time = word_info.start_time.total_seconds()
                end_time = word_info.end_time.total_seconds()
                transcription.append({
                    "text": word_info.word.strip(),
                    "start_time": start_time,
                    "end_time": end_time
                })
        transcription_text = " ".join([entry["text"] for entry in transcription])

      
        ai_normalized_terms = ai_normalize_with_modus(transcription_text)
        print("here", ai_normalized_terms)
     
        subtitle_track = []
        for entry in transcription:
            text = entry["text"].lower()
            start_time = entry["start_time"]
            end_time = entry["end_time"]

            for term in ai_normalized_terms:
                if term.lower() in text:
                    dgraph_result = query_dgraph(term, "Soccer")
                 
                    if dgraph_result:
                        subtitle_track.append({
                            "term": term,
                            "start_time": start_time,
                            "end_time": end_time,
                            "animation": dgraph_result[0].get("animation"),
                            "intensity": dgraph_result[0].get("intensity")
                        })
                    else:
                        cleaned_term = term.rstrip("!").lower() 
                        exclamation_count = term.count("!")
                        if exclamation_count == 2:
                            intensity = "High"
                        elif exclamation_count == 1:
                            intensity = "Medium"
                        else:
                            intensity = "Low"
                        subtitle_track.append({
                            "term": cleaned_term,
                            "start_time": start_time,
                            "end_time": end_time+2,
                            "intensity": intensity
                        })

        subtitle_path = Path(UPLOAD_DIR) / "subtitle_track.json"
        with open(subtitle_path, "w") as f:
            json.dump(subtitle_track, f)

        
        output_video_path = Path(UPLOAD_DIR) / "output_video.mp4"
        images_path = Path("../../Sign-Language-Subtitles/images") 

        command = [
            "../../Sign-Language-Subtitles/build/video_overlay",
            str(original_video_path),
            str(subtitle_path),
            str(images_path),
            str(output_video_path)
        ]

        subprocess.run(command, check=True)

        return FileResponse(
            path=output_video_path,
            media_type="video/mp4",
            filename="processed_video.mp4"
        )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Video processing failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process video: {e}")
    finally:
    
        if original_video_path.exists():
            os.remove(original_video_path)
        if audio_path.exists():
            os.remove(audio_path)




def query_dgraph(phrase_text: str, sport: str):
    """
    Query Dgraph to retrieve animations and metadata for a given phrase and sport.
    """
    query = """
    query($text: String!, $sport: String!) {
      queryPhrase(filter: {text: {eq: $text}, sport: {eq: $sport}}) {
        text
        sport
        intensity
        animation
      }
    }
    """
    variables = {"text": phrase_text, "sport": sport}
    try:
        response = requests.post(
            DGRAPH_GRAPHQL_ENDPOINT,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

    
        if "errors" in data:
            raise HTTPException(status_code=500, detail=data["errors"])

        return data.get("data", {}).get("queryPhrase", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query Dgraph: {e}")


@app.post("/query-phrase")
def get_phrase_metadata(query: PhraseQuery):
    """
    Endpoint to retrieve metadata and animation details for a phrase and sport.
    """
    results = query_dgraph(query.phrase, query.sport)
    if not results:
        return {"message": "No data found for the provided phrase and sport"}
    
    return {"message": "Query successful", "data": results}