from ninja import Router
from .models import UserDevice, DeviceStatus
from apps.accounts.schemas import UserSchema # Use existing schemas where possible
from core.responses import success_response, error_response, StandardResponse
from core.permissions import AuthBearer # Need to verify if admin check is needed

router = Router()

@router.get("/pending", auth=AuthBearer(), response={200: StandardResponse})
def list_pending_devices(request):
    if not request.auth.is_staff:
        return error_response("ERR_403", "Admin access required")
    
    devices = UserDevice.objects.filter(status=DeviceStatus.PENDING)
    data = [
        {
            "id": str(d.id),
            "user": d.user.name,
            "install_id": d.install_id,
            "platform": d.platform,
            "device_model": d.device_model,
            "created_at": d.created_at
        } for d in devices
    ]
    return success_response(data=data)

@router.post("/{device_id}/approve", auth=AuthBearer(), response={200: StandardResponse})
def approve_device(request, device_id: str):
    if not request.auth.is_staff:
        return error_response("ERR_403", "Admin access required")
    
    device = UserDevice.objects.get(id=device_id)
    device.status = DeviceStatus.APPROVED
    device.save()
    return success_response(data={"message": "Device approved"})

@router.post("/{device_id}/block", auth=AuthBearer(), response={200: StandardResponse})
def block_device(request, device_id: str):
    if not request.auth.is_staff:
        return error_response("ERR_403", "Admin access required")
    
    device = UserDevice.objects.get(id=device_id)
    device.status = DeviceStatus.BLOCKED
    device.save()
    return success_response(data={"message": "Device blocked"})
