# ===================== IMPORTS =====================
import os
import torch
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages

from diffusers import StableDiffusionPipeline

from users.forms import UserRegistrationForm
from .models import UserRegistrationModel


# ===================== AUTH VIEWS =====================

def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You have been successfully registered')
            return render(request, 'UserRegistrations.html', {'form': UserRegistrationForm()})
        else:
            messages.error(request, 'Email or Mobile already exists')
    else:
        form = UserRegistrationForm()
    return render(request, 'UserRegistrations.html', {'form': form})


def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('pswd')

        try:
            user = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            if user.status == "activated":
                request.session['id'] = user.id
                request.session['loggeduser'] = user.name
                return render(request, 'users/UserHomePage.html')
            else:
                messages.error(request, 'Account not activated')
        except:
            messages.error(request, 'Invalid Login ID or Password')

    return render(request, 'UserLogin.html')


def UserHome(request):
    return render(request, 'users/UserHomePage.html')


#========= GLOBAL SETTINGS =====================
MODEL_ID = "runwayml/stable-diffusion-v1-5"
DEVICE = "cpu"   # CPU only (safe for Windows)

pipe = None  # Lazy-loaded pipeline (VERY IMPORTANT)

# ===================== STRONG STYLE PROMPTS =====================
STYLE_PROMPTS = {
    "algerian": (
    "single centered object, Algerian traditional art style, "
    "North African cultural aesthetics, Amazigh and Islamic motifs, "
    "hand-painted illustration, rich warm colors, ornamental details, "
    "authentic Maghreb artistic influence, clean background, "
    "no repetition, no patterns, no abstract design"
),


    "iconic": (
    
    "single centered object, clean iconic vector illustration, "
    "flat design, bold outlines, minimal color palette, "
    "white background, product illustration, no patterns, "
    "no repetition, no background texture"
),

    
    "realistic": (
    "single realistic object, ultra realistic photograph, "
    "studio lighting, sharp focus, isolated on white background, "
    "high detail, professional product photography"
),

}

NEGATIVE_PROMPT = (
    "man, men, boy, male, dog, animals, road, walking, "
    "blurry, low quality, distorted, extra limbs, watermark"
)


# ===================== PIPELINE LOADER =====================
def get_pipeline():
    global pipe
    if pipe is None:
        pipe = StableDiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            use_auth_token=True,     # 🔐 important
            resume_download=True     # 🔄 avoids re-download
        )
        pipe.enable_attention_slicing()
        pipe.to(DEVICE)
    return pipe


# ===================== HOME =====================
def UserHome(request):
    return render(request, "users/UserHomePage.html")


# ===================== TEXT TO IMAGE =====================
def test_text_to_image(request):
    if request.method == "POST":
        description = request.POST.get("description")
        style = request.POST.get("style", "realistic")

        if not description:
            messages.error(request, "Please enter a description")
            return render(request, "users/test_form.html")

        # Get style prompt
        style_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["realistic"])

        # Final prompt (base paper compliant)
        final_prompt = f"{description}, {style_prompt}"

        try:
            pipe = get_pipeline()

            # Generate image
            image = pipe(
                final_prompt,negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=45,   # Reduced for CPU speed
                guidance_scale=8.5
            ).images[0]

            # Save image
            filename = f"generated_{style}.png"
            save_path = os.path.join(settings.MEDIA_ROOT, filename)
            image.save(save_path)

            return render(
                request,
                "users/test_form.html",
                {
                    "path": settings.MEDIA_URL + filename,
                    "text": description,
                    "style": style,
                }
            )

        except Exception as e:
            messages.error(request, f"Image generation failed: {str(e)}")
            return render(request, "users/test_form.html")

    # GET request
    return render(request, "users/test_form.html")

def Leaf_Predictions(request):
    if request.method == 'POST':
        myfile = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        # from .utility import leafPredictionModel
        # result, test_img = leafPredictionModel.predict_leaf(filename)
        path = os.path.join(settings.MEDIA_ROOT, filename)
        result = script.analysis(path)
        print('Result:', result)
        return render(request, "users/leaf_form.html", {"result": result, "path": uploaded_file_url})
    else:
        return render(request, "users/leaf_form.html", {})
