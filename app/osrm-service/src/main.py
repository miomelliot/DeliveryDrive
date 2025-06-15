app = FastAPI(title="orm-service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Или ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
