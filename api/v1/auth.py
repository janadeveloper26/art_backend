from ninja import Router

router = Router()

@router.post("/login")
def login(request):
    return {"message": "Login endpoint placeholder"}

@router.post("/register")
def register(request):
    return {"message": "Register endpoint placeholder"}
