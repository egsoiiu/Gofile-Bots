# 🤖 GoFile Uploader Bot

A powerful Telegram bot that helps you upload files or download links directly to [GoFile.io](https://gofile.io) — fast, simple, and secure.

---

## 📖 How to Use

### 📁 Upload from Telegram
1. **Send** me any file (document, image, video, etc.)
2. **Reply** to the file with `/upload`
3. (Optional) Add your **GoFile token** and **folderId**
   - `/upload your_token`
   - `/upload your_token folderId`

### 🌐 Upload from a Direct Download Link
1. Send a command like:
   - `/upload https://example.com/file.zip`
   - `/upload https://example.com/file.zip your_token`
   - `/upload https://example.com/file.zip your_token folderId`

---

## ⭐ Bot Features

| Feature            | Description                                             |
|--------------------|---------------------------------------------------------|
| 📤 File Upload     | Upload any file from Telegram to GoFile                |
| 🔗 Link Support    | Upload files from direct download links                |
| 📁 Custom Folders  | Save files to specific GoFile folders                  |
| 🔐 Token Support   | Use your personal GoFile token for account access      |
| ⚡ Fast Speeds     | Quick uploads and instant GoFile links                 |
| 🧼 Auto-Cleanup    | Option to delete uploaded files from GoFile            |
| 📦 All File Types  | Supports documents, videos, images, music, etc.        |

---

## 📥 Environment Variables

```
API_ID
API_HASH
BOT_TOKEN

```

---

## 🧹 Deleting Uploaded Files

If your file was uploaded with a **Guest token** or your account token, you can delete it:

#### Example:
```python
import requests

def delete_uploaded_file():
    file_id = "163230e0-0906-45b5-b6ff-e140ecd72382"
    guest_token = "tKb1w1MlUogN6OWkDUkB0JGEH2oghEpu"

    url = "https://api.gofile.io/deleteContent"
    params = {
        "contentId": file_id,
        "token": guest_token
    }

    response = requests.delete(url, params=params)
    result = response.json()

    if result["status"] == "ok":
        print("✅ File deleted successfully.")
    else:
        print("❌ Failed to delete:", result.get("status"))
```

---

## 💡 Notes

- Files uploaded without a token are stored under a temporary **Guest session**.
- Guest tokens expire after inactivity; store them if you need to delete later.
- GoFile does **not require an account**, but using one lets you manage uploads better.

---

## 🧑‍💻 Developer Info

- 🔗 [GoFile API Docs](https://gofile.io/api)
- Built with `requests`, `shlex`, `subprocess`, and `Python 3.8+`
- Supports deployment on bots, servers, or CLI tools

---

## 📌 Disclaimer

This project is not affiliated with GoFile.io. Use responsibly. Uploaded content must comply with all applicable laws and GoFile's [Terms of Service](https://gofile.io/terms).

---

## 🚀 Start Now!

Just send a file or use the `/upload` command — GoFile Uploader Bot will take care of the rest!
