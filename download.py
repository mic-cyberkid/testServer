import requests
import re

def download(file_id, destination):
    session = requests.Session()
    base_url = "https://drive.usercontent.google.com/download"

    params = {"id": file_id, "export": "download"}
    response = session.get(base_url, params=params, stream=True)

    if "text/html" in response.headers.get("Content-Type", ""):
        # We must extract the confirm token from the HTML
        html = response.text
        token_match = re.search(r'name="confirm" value="([^"]+)"', html)

        if not token_match:
            raise RuntimeError("Could not find confirm token in response HTML!")

        token = token_match.group(1)
        params["confirm"] = token
        print("Downloading file....")
        response = session.get(base_url, params=params, stream=True)

    save_file(response, destination)


def save_file(response, filename):
    with open(filename, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)


if __name__ == "__main__":
    download("1tiwRInMk075NyweRBiMPJhDAAUbVmIxq",
             "PhysicsChatbotServer-Windows.zip")
    print("Download complete")
