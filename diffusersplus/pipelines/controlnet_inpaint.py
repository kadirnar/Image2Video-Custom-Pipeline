from typing import List, Optional

import torch
from diffusers import ControlNetModel, StableDiffusionControlNetInpaintPipeline
from PIL import Image

from diffusersplus.pipelines.base import BaseDiffusionModel
from diffusersplus.preprocces import preprocces_dicts
from diffusersplus.utils.data_utils import load_and_resize_image


class StableDiffusionControlNetInpaintGenerator(BaseDiffusionModel):
    """
    A class to handle image inpainting using stable diffusion and control net models.
    """

    def __init__(
        self,
        stable_model_id: str = "runwayml/stable-diffusion-v1-5",
        controlnet_model_id: str = "lllyasviel/sd-controlnet-canny",
        scheduler_name: str = "DDIM",
    ):
        super().__init__()
        self.stable_model_id = stable_model_id
        self.controlnet_model_id = controlnet_model_id
        self.scheduler_name = scheduler_name

    def _load_diffusion_pipeline(self):
        """
        Load the stable diffusion inpainting pipeline with control net model.
        """
        if not hasattr(self, "pipe") or self.pipe is None:
            controlnet = ControlNetModel.from_pretrained(self.controlnet_model_id, torch_dtype=torch.float16)
            self.pipe = StableDiffusionControlNetInpaintPipeline.from_pretrained(
                pretrained_model_name_or_path=self.stable_model_id,
                controlnet=controlnet,
                safety_checker=None,
                torch_dtype=torch.float16,
            )
            self.load_scheduler("stable", self.stable_model_id, self.scheduler_name)

    def __call__(
        self,
        image_path: str,
        mask_path: str,
        prompt: str = "A fully restored image.",
        negative_prompt: str = "bad",
        height: int = 512,
        width: int = 512,
        preprocess_type: str = "Canny",
        resize_type: str = "center_crop_and_resize",
        strength: float = 0.5,
        guess_mode: bool = False,
        num_images_per_prompt: int = 1,
        num_inference_steps: int = 20,
        guidance_scale: int = 7.0,
        controlnet_conditioning_scale: int = 1.0,
        generator_seed: int = 0,
    ) -> torch.Tensor:
        """
        Generate an inpainted image based on the provided parameters.
        """

        # Modeli yükle
        self._load_diffusion_pipeline()

        # Load image, mask and preprocess
        read_image = load_and_resize_image(image_path=image_path, resize_type=resize_type, height=height, width=width)
        mask_image = load_and_resize_image(image_path=mask_path, resize_type=resize_type, height=height, width=width)
        control_image = preprocces_dicts[preprocess_type](read_image)

        generator = self._configure_random_generator(generator_seed)

        # Generate the inpainted image
        output = self.pipe(
            prompt=prompt,
            height=height,
            width=width,
            guess_mode=guess_mode,
            control_image=control_image,
            mask_image=mask_image,
            image=read_image,
            strength=strength,
            negative_prompt=negative_prompt,
            num_images_per_prompt=num_images_per_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            controlnet_conditioning_scale=float(controlnet_conditioning_scale),
            generator=generator,
        ).images

        return output
