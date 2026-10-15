"""Start the studio API. Default http://127.0.0.1:8876"""
from studio.app import create_app
from studio.config import api_port, bind_host

app = create_app()

if __name__ == "__main__":
    import uvicorn

    print(
        f"Cognitive Value Studio API | shadow mode | http://{bind_host()}:{api_port()}",
        flush=True,
    )
    uvicorn.run(app, host=bind_host(), port=api_port())
