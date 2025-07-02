from app.main import run


def dev():
    import uvicorn
    uvicorn.run(
        "app.main:app",
        reload=True,
        host="0.0.0.0",
        port=8000,
        log_config="app/core/config/log_config.json"
    )


if __name__ == '__main__':
    # uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-config app\core\config\log_config.json
    run()
