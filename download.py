import requests
import re
from tqdm import tqdm

def download(file_url, destination):
    session = requests.Session()

    # First request to retrieve confirm page + hidden form values
    response = session.get(file_url, stream=True)

    if "text/html" in response.headers.get("Content-Type", ""):
        html = response.text

        hidden_inputs = dict(re.findall(
            r'<input type="hidden" name="([^"]+)" value="([^"]+)"', html
        ))

        if not hidden_inputs:
            raise RuntimeError("Error: No hidden form fields found! Page format changed?")

        download_url = "https://drive.usercontent.google.com/download"
        print("\nBypassing security scan...")

        response = session.get(download_url, params=hidden_inputs, stream=True)

    save_file_with_progress(response, destination)


def save_file_with_progress(response, filename):
    total_size = int(response.headers.get('Content-Length', 0))
    chunk_size = 32768  # 32 KB

    with open(filename, "wb") as f, tqdm(
        total=total_size, unit='B', unit_scale=True, desc=filename, ascii=True
    ) as pbar:
        for chunk in response.iter_content(chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))


if __name__ == "__main__":
    download(
        "https://drive.usercontent.google.com/u/0/uc?id=1vRvQlP9mta5txhGOaJtIRbRlg68JyIt0&export=download",
        "PhysicsChatbotServer-Windows.zip"
    )
    print("\n✅ Download complete!")
