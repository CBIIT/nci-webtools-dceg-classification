# Client

```sh
npx http-server client --proxy http://127.0.0.1:9000
```

# Server
```sh
cd server
python3 -m pip install -r requirements.txt

# production
gunicorn server:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:9000

# development
uvicorn server:app --workers 4 --host 0.0.0.0 --port 9000
```