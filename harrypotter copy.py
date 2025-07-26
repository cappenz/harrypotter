import os
import sounddevice as sd
import scipy.io.wavfile as wavfile
import openai
import whisper
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save
import requests
import os
import time
import logging
from dotenv import load_dotenv
from typing import override
import requests
import cv2
import subprocess
import platform





openai.api_key = ("")#paste openai api key here
elevenlabs_api_key = ("")#paste elevenlabs api key here
# Load environment variables from .env file
# on space bar pressed record audio
# on space bar relased transcribe audio with whisper
#send transcription to headra and open that full screen 

answer=""

def asking(answer,openai):
    # set up
    number0=0
    number1=0
    #ask user if they have something to say
    answer = input("Do you have something to say? (yes/no)")
    number0= number0+2
    number1 = number1+3
    #if input containes yes

    if "yes" in answer: 
        #record audio (take a few seconds to activate)
        freq = 44100
        duration = 5
        #record audio
        recording = sd.rec(int(duration * freq), 
                        samplerate=freq, channels=1)
        sd.wait()
        wavfile.write(f"recording{number0}.wav", freq, recording)
        wavfile.write(f"recording{number1}.wav", freq, recording)
        # use whisper to transcribe
       
        model = whisper.load_model("turbo")
        result = model.transcribe(f"recording{number1}.wav")
        print(result["text"])
        #send to chatgpt for answers
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"Write an answer as if you were a Harry Potter talking painting to this comment: {result['text']}"
                }
            ]
        )
        print(response.choices[0].message.content)

        #elevenlabs
        client = ElevenLabs(api_key=elevenlabs_api_key)

        audio = client.text_to_speech.convert(
            text=response.choices[0].message.content,
            voice_id="l0jEJEG5ZuUd9SnkaVdv",
            model_id="eleven_turbo_v2_5"
        )

        output_path = (f"EL_recording{number1}.wav")
        # Magic Python syntactic to join all the chunks into one big blob
        buf = b"".join(audio);
        # Now both playing and saving works. Wohoo!
        play(buf)
        save(buf, output_path)

        logger = logging.getLogger()
        logging.basicConfig(level=logging.WARNING)  # Change from INFO to WARNING to reduce output


        class Session(requests.Session):
            def __init__(self, api_key: str):
                super().__init__()

                self.base_url: str = "https://api.hedra.com/web-app/public"
                self.headers["x-api-key"] = api_key

            @override
            def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
                request.url = f"{self.base_url}{request.url}"

                return super().prepare_request(request)


        def main():
            # Load environment variables from .env file
   
            api_key = ""#paste hedra api key here


            # Initialize Hedra client
            session = Session(api_key)

            model_id = "d1dd37a3-e39a-4854-a298-6510289f9cf2"

            # Use hardcoded values for the script
            image_path = "/Users/charlotteappenzeller/dev/harrypotter/fatlady.jpg"
            audio_path = f"/Users/charlotteappenzeller/dev/harrypotter/EL_recording{number1}.wav"
            text_prompt = "your a harrypotter talking painting"
            resolution = "720p"
            aspect_ratio = "16:9"
            duration = 10.0

            image_response = session.post(
                "/assets",
                json={"name": os.path.basename(image_path), "type": "image"},
            )
            if not image_response.ok:
                logger.error(
                    "error creating image: %d %s",
                    image_response.status_code,
                    image_response.json(),
                )
                return
            image_id = image_response.json()["id"]
            with open(image_path, "rb") as f:
                session.post(f"/assets/{image_id}/upload", files={"file": f}).raise_for_status()

            audio_id = session.post(
                "/assets", json={"name": os.path.basename(audio_path), "type": "audio"}
            ).json()["id"]
            with open(audio_path, "rb") as f:
                session.post(f"/assets/{audio_id}/upload", files={"file": f}).raise_for_status()

            generation_request_data = {
                "type": "video",
                "ai_model_id": model_id,
                "start_keyframe_id": image_id,
                "audio_id": audio_id,
                "generated_video_inputs": {
                    "text_prompt": text_prompt,
                    "resolution": resolution,
                    "aspect_ratio": aspect_ratio,
                },
            }

            # Add optional parameters if provided
            if duration is not None:
                generation_request_data["generated_video_inputs"]["duration_ms"] = int(duration * 1000)

            generation_response = session.post(
                "/generations", json=generation_request_data
            ).json()
            generation_id = generation_response["id"]
            while True:
                status_response = session.get(f"/generations/{generation_id}/status").json()
                status = status_response["status"]

                # --- Check for completion or error to break the loop ---
                if status in ["complete", "error"]:
                    break

                time.sleep(5)

            # --- Process final status (download or log error) ---
            if status == "complete" and status_response.get("url"):
                download_url = status_response["url"]
                # Use asset_id for filename if available, otherwise use generation_id
                output_filename_base = status_response.get("asset_id", generation_id)
                output_filename = f"{output_filename_base}.mp4"
                try:
                    # Use a fresh requests get, not the session, as the URL is likely presigned S3
                    with requests.get(download_url, stream=True) as r:
                        r.raise_for_status() # Check if the request was successful
                        with open(output_filename, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to download video: {e}")
                except IOError as e:
                    logger.error(f"Failed to save video file: {e}")
            elif status == "error":
                logger.error(f"Video generation failed: {status_response.get('error_message', 'Unknown error')}")
            else:
                # This case might happen if loop breaks unexpectedly or API changes
                logger.warning(f"Video generation finished with status '{status}' but no download URL was found.")


             # Open the video file with audio using system default player
            video_path = f"/Users/charlotteappenzeller/dev/harrypotter/{output_filename_base}.mp4"
            print(f"Opening video with audio: {video_path}")
            
            # Use system default video player (supports audio)
            
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", video_path])
                elif platform.system() == "Windows":
                    subprocess.run(["start", video_path], shell=True)
                else:  # Linux
                    subprocess.run(["xdg-open", video_path])
                
                print("Video opened in system player. Close the video player to continue.")
                input("Press Enter when you're done watching the video...")
                
            except Exception as e:
                print(f"Error opening video: {e}")
                print("Trying alternative method...")
                
                # Fallback to cv2 (video only, no audio)
                cap = cv2.VideoCapture(video_path)
                cv2.namedWindow("Video", cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty("Video", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    cv2.imshow("Video", frame)

                    # Press 'q' to exit
                    if cv2.waitKey(25) & 0xFF == ord('q'):
                        break

                cap.release()
                cv2.destroyAllWindows()

        if __name__ == "__main__":
            main()

    else:
        #if no recording made, say no recording made
        print("No recording made")
    
    # Restart the function after video finishes or if no recording was made
    asking(answer, openai)

#start the program
asking(answer, openai)
