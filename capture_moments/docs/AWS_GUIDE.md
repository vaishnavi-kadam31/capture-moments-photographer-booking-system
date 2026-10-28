# AWS Guide (Phase 2) – S3 + IAM + EC2

> **Not yet tested.** The code hooks exist in `config/settings.py` (the `USE_S3` switch) and the steps below
> follow standard AWS/Django practice, but nobody has run this deployment. Do the verification step at the end of
> each section before moving on, and don't write "works on AWS" in your report until you've seen it work.

## 0. Before you start
1. Local version must pass `python manage.py test` and the manual checklist.
2. Create an AWS account. **Set a billing alarm** (Billing → Budgets → e.g. ₹500/month).
3. Pick one region and stay in it. Examples below use **ap-south-1 (Mumbai)**.

## What each service does here
| Service | Job in this project |
|---|---|
| **EC2** | A small Linux server that runs Django (via gunicorn + nginx) |
| **S3** | Stores uploaded photos (profile pictures + portfolio) |
| **IAM** | Lets the EC2 server read/write *only* your bucket – no passwords in code |
| **DynamoDB** | *Not used.* See the note at the end |

## 1. S3 bucket (image storage)
1. S3 → **Create bucket**. Name must be globally unique, e.g. `capture-moments-yourname-2026`. Region: ap-south-1.
2. Keep **Block all public access = ON**. The app uses temporary signed links, so the bucket stays private.
3. Create the bucket.

## 2. IAM role for the server
1. IAM → Policies → **Create policy** → JSON (replace `YOUR-BUCKET`):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": "arn:aws:s3:::YOUR-BUCKET" },
    { "Effect": "Allow", "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET/*" }
  ]
}
```
   Name it `CaptureMomentsS3Access`.
2. IAM → Roles → **Create role** → trusted entity **AWS service → EC2** → attach that policy → name `CaptureMomentsEC2Role`.

## 3. Launch the EC2 server
1. EC2 → **Launch instance**: Ubuntu Server 24.04 LTS, type `t3.micro` (or `t2.micro` – whichever is free-tier for your account).
2. Create/download a key pair (`.pem`) – keep it safe.
3. Network settings → security group inbound rules: **SSH (22)** from *My IP* only, **HTTP (80)** from anywhere.
4. Advanced details → **IAM instance profile** = `CaptureMomentsEC2Role`.
5. Launch, then note the **Public IPv4 DNS**.

## 4. Install the app on the server
```bash
ssh -i yourkey.pem ubuntu@<public-dns>

sudo apt update && sudo apt install -y python3-venv python3-pip nginx git
# copy your project here – e.g. from your PC:  scp -i yourkey.pem -r capture_moments ubuntu@<public-dns>:~
cd ~/capture_moments
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-aws.txt
```

Create `/home/ubuntu/capture_moments/.env` (see `.env.example`) and fill in the real values.
Generate a secret key with: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`.

```bash
set -a; source .env; set +a          # loads the variables into this terminal
python manage.py makemigrations accounts photographers bookings
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data
python manage.py createsuperuser
```

## 5. Run with gunicorn + nginx
`/etc/systemd/system/capture.service`
```ini
[Unit]
Description=Capture Moments (gunicorn)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/capture_moments
EnvironmentFile=/home/ubuntu/capture_moments/.env
ExecStart=/home/ubuntu/capture_moments/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```
`/etc/nginx/sites-available/capture`
```nginx
server {
    listen 80;
    server_name _;
    client_max_body_size 12M;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now capture
sudo ln -s /etc/nginx/sites-available/capture /etc/nginx/sites-enabled/capture
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```
Static files (CSS/JS) are served by WhiteNoise inside Django, so nginx only forwards requests.

## 6. Verify (do all of these)
1. Open `http://<public-dns>/` – home page with styling.
2. Register a photographer, upload a portfolio image.
3. S3 console → your bucket → you should see `portfolio/…` and `profiles/…` objects. **That proves S3 works.**
4. Right-click the image on the site → open in new tab: the URL contains `X-Amz-Signature` (signed link).
5. Try opening the plain object URL from the S3 console in a private window – it should say *Access Denied* (bucket is private, as intended).
6. If images fail to upload, run `sudo journalctl -u capture -n 50` and read the error.

## 7. Limits you should mention in your report
* Plain HTTP only. For HTTPS you need a domain name and a certificate (e.g. certbot/Let's Encrypt, or an Application Load Balancer + ACM).
* SQLite on the server's disk is lost if the instance is terminated. For real use, move to **Amazon RDS (PostgreSQL)** by changing `DATABASES` in `settings.py`.
* The public IP changes if you stop/start the instance (use an Elastic IP if needed).
* **Delete resources when done** (terminate EC2, empty and delete the bucket) to avoid charges.

## Is DynamoDB needed?
Honestly: **no.** Bookings, users and profiles are relational data (bookings point to clients and photographers, you
filter and join them). SQLite/PostgreSQL fits this naturally; forcing it into DynamoDB would add complexity without
benefit. A reasonable, *optional* use of DynamoDB would be a high-volume, key-value style store such as a
notification/activity log keyed by user id. **That is not implemented** in this project. In your report you can
justify the decision: "SQL database for relational booking data, S3 for files, DynamoDB considered but not required."
Optional future work: Amazon SES for real emails, RDS for the database.
