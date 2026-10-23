# generate_qrcodes.py
import os
import qrcode
from database.connection import get_connection


def generate_all_qrcodes():
    conn = get_connection()
    if conn is None:
        print("DB Connection failed")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT asset_code FROM assets")
        assets = cursor.fetchall()

        qr_dir = "static/uploads/qrcodes"
        os.makedirs(qr_dir, exist_ok=True)

        count = 0
        for asset in assets:
            code = asset["asset_code"]
            if not code: continue

            file_path = os.path.join(qr_dir, f"{code}.png")

            # Generate only if file doesn't exist
            if not os.path.exists(file_path):
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(f"ASSET:{code}")
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(file_path)
                print(f"✅ Generated QR Code for: {code}")
                count += 1

        print(f"\nDone! Generated {count} QR code images.")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()


if __name__ == "__main__":
    generate_all_qrcodes()