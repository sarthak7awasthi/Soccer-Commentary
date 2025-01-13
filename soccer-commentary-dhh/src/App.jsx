import { useState } from "react";
import axios from "axios";
import { Player } from "@lottiefiles/react-lottie-player";
import videoCamAnimation from "./animation/processing.json";
import "./App.css";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [responseVideoUrl, setResponseVideoUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  const [showAnimation, setShowAnimation] = useState(false);
  const [showContent, setShowContent] = useState(false);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setResponseVideoUrl("");
    setError("");
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a video file first.");
      return;
    }

    setIsUploading(true);
    setError("");
    setResponseVideoUrl("");
    setShowAnimation(true);
    setShowContent(false);

    setTimeout(() => {
      setShowAnimation(false);
      setShowContent(true);
    }, 3000);

    try {
      const formData = new FormData();
      formData.append("video", selectedFile);

      const serverUrl = process.env.REACT_APP_SERVER_URL;

      const response = await axios.post(serverUrl, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const { videoUrl } = response.data;
      setResponseVideoUrl(videoUrl || "");
    } catch (err) {
      console.error(err);
      setError("Something went wrong while uploading. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="App soccer-bg">
      <h1>{`Soccer Commentary (DHH)`}</h1>
      <div className="upload-container">
        <p>Upload your short soccer video below!</p>

        <input type="file" accept="video/*" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={isUploading}>
          {isUploading ? "Uploading..." : "Upload Video"}
        </button>

        {showAnimation && (
          <div className="animation-container">
            <Player
              autoplay
              loop
              src={videoCamAnimation}
              style={{ height: "200px", width: "200px" }}
            />
          </div>
        )}
      </div>

      <>
        {error && <p className="error-message">{error}</p>}
        {showContent && responseVideoUrl && (
          <div className="video-container">
            <h2>Uploaded Video Response</h2>
            <video
              controls
              src={responseVideoUrl}
              className="responsive-video"
            />
          </div>
        )}
      </>
    </div>
  );
}

export default App;
