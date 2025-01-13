# Sign-Language Subtitles for Sports Commentary

An innovative platform designed to improve accessibility by translating sports commentary into synchronized sign-language animations, enabling the Deaf and Hard-of-Hearing community to enjoy sports content inclusively.

## Table of Contents

1. [Features](#features)
2. [Why and How Modus is Used](#why-and-how-modus-is-used)
3. [Why and How Dgraph is Used](#why-and-how-dgraph-is-used)
4. [Technologies Used](#technologies-used)
5. [Prerequisites](#prerequisites)
6. [Installation](#installation)
7. [Directory Structure](#directory-structure)
8. [API Endpoints](#api-endpoints)
9. [Video Overlay Program](#video-overlay-program)
10. [Known Issues](#known-issues)
11. [Future Improvements](#future-improvements)
12. [Contributing](#contributing)
13. [License](#license)

## Features

- **Video Upload**: Support for sports commentary video uploads (.mp4)
- **Audio Extraction**: Automated audio extraction using FFmpeg
- **Speech-to-Text Transcription**: Integration with Google Cloud Speech-to-Text
- **AI-Based Normalization**: Utilizes Modus AI for context-aware transcription normalization
- **Metadata Retrieval**: Dgraph-powered knowledge graph for animation and metadata storage
- **Subtitle Track Generation**: JSON-based subtitle tracks with timing and animation data
- **Video Overlay**: C++ library for embedding sign-language animations
- **Processed Video Delivery**: Final video output with synchronized animations

## Why and How Modus is Used

### Why Modus?

* Modus integrates pre-trained large language models (e.g., LLaMA) to handle complex transcription normalization tasks.
* It interprets context, synonyms, and domain-specific terms dynamically, ensuring precise and versatile normalization across various sports.

### How Modus is Used

1. **Normalization**:
   * Raw transcription text is sent to Modus via a GraphQL query.
   * Modus processes the text, providing normalized terms formatted as `[term1, term2, ...]`.

2. **Integration in FastAPI**:
   * Modus is hosted locally (`http://localhost:8686/graphql`) and queried from the FastAPI backend for real-time inference.

3. **Use Cases**:
   * Standardizing commentary phrases (e.g., "He scores!" → "goal").
   * Extracting key terms for querying metadata in Dgraph.

## Why and How Dgraph is Used

### Why Dgraph?

* Dgraph serves as the knowledge graph backend, efficiently storing relationships between terms, animations, synonyms, and intensity levels.
* Its GraphQL-based querying ensures low-latency retrieval of metadata for overlay generation.

### How Dgraph is Used

1. **Schema Definition**:
   * The schema includes entities like terms, synonyms, intensity levels, and animations.

2. **Metadata Storage**:
   * Terms (e.g., "goal") are linked to animations (e.g., `goal_loud.mp4`), synonyms, and intensity mappings.

3. **Query Integration**:
   * Queries are made to Dgraph via the FastAPI backend for animations and metadata corresponding to normalized terms.

4. **Use Cases**:
   * Retrieve animations (e.g., "goal_standard.mp4") for specific terms.
   * Provide additional metadata like intensity for customization.

## Technologies Used

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Audio/Video Processing | FFmpeg, C++ (video_overlay) |
| AI Normalization | Modus (LLaMA-based NLP) |
| Knowledge Graph | Dgraph |
| Transcription Service | Google Cloud Speech-to-Text |
| Deployment | Docker, Google Cloud Platform (GCP) |

![diagram-export-1-13-2025-3_08_51-AM](https://github.com/user-attachments/assets/96b608e1-a680-4a80-998f-f0ad4fbf3679)






## Prerequisites

- Python 3.8+
- FFmpeg installed and added to system path
- C++ compiler
- Google Cloud credentials
- Running instances of Modus and Dgraph

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-repo/sign-language-subtitles.git
cd sign-language-subtitles
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Modus:
   - Install and run Modus locally (http://localhost:8686/graphql)

4. Set up Dgraph:
   - Define schema and populate initial data

5. Build the C++ overlay program:
   - Ensure video_overlay is compiled in Sign-Language-Subtitles/build/

6. Start the FastAPI application:
```bash
uvicorn main:app --reload
```

## Directory Structure

```
project-root/
├── main.py                     # FastAPI backend code
├── uploads/                    # Temporary storage for files
├── Sign-Language-Subtitles/    # C++ video overlay program
│   ├── build/                  # Compiled binaries
│   │   ├── video_overlay      # C++ program for overlay
│   ├── images/                # Static images for overlay
├── app/
│   ├── service-account-key.json # Google Cloud credentials
├── requirements.txt           # Python dependencies
```

## API Endpoints

| Endpoint | Method | Description |
|----------|---------|------------|
| /transcribe-audio | POST | Upload video, process, and return with overlays |
| /query-phrase | POST | Query metadata and animations for specific terms |

### Example Usage

```bash
curl -X POST "http://localhost:8000/transcribe-audio" \
-H "Content-Type: multipart/form-data" \
-F "file=@input_video.mp4" --output processed_video.mp4
```

## Video Overlay Program

The C++ video_overlay library accepts:
- Input video
- Subtitle track JSON
- Static images directory
- Output path

Usage:
```bash
./video_overlay input_video.mp4 subtitle_track.json images output_video.mp4
```

## Known Issues

- **High Latency**: Speech-to-Text transcription can be slow for longer videos
- **Missing Dgraph Data**: Ensure complete term coverage in Dgraph schema
- **File Cleanup**: Implement scheduled cleanup for temporary files

## Future Improvements

- Real-time processing for live commentary streams
- React-based frontend interface
- Fine-tuned AI models for sports-specific terminology

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed explanation

## License

This project is licensed under the MIT License. See LICENSE for details.
