from app.main import start, dev


if __name__ == '__main__':
    # uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-config app\core\config\log_config.json
    start()
