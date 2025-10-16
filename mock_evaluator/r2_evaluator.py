from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import uvicorn

app = FastAPI(title="Evaluator API")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


@app.post("/evaluate")
async def evaluate(request: Request):
    """
    Receives a JSON payload containing EVAL_REQUEST data.
    Logs the request and returns a 200 OK response with acknowledgment.
    """
    try:
        data = await request.json()
        logging.info("📩 Received POST /evaluate")
        logging.info(data)

        # You could validate here if "EVAL_REQUEST" key is expected
        if not isinstance(data, dict):
            return JSONResponse(content={"error": "Invalid payload"}, status_code=400)

        # Example: Confirm we received the expected structure
        logging.info(f"EVAL_REQUEST received for task: {data.get('task', '(unknown task)')}")  # type: ignore

        # Respond with success confirmation
        return JSONResponse(
            content={
                "status": "ok",
                "message": "Evaluation request logged successfully.",
            },
            status_code=200,
        )

    except Exception as e:
        logging.exception("❌ Error processing evaluation request")
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run("r1_evaluator:app", host="0.0.0.0", port=8082, reload=True)
