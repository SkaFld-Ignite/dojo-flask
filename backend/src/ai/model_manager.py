"""
Model Manager for loading and managing AI models (LLM and ASR)
"""

import os
import torch
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

class ModelManager:
    """Singleton model manager for loading and caching AI models"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._models = {}
        self._device = self._get_device()
        self._model_cache_dir = Path(os.getenv('MODEL_CACHE_DIR', './models'))
        self._model_cache_dir.mkdir(exist_ok=True)
        self._initialized = True
        
        logger.info(f"ModelManager initialized with device: {self._device}")
    
    def _get_device(self) -> str:
        """Determine the best available device for inference"""
        
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"CUDA available: {torch.cuda.get_device_name()}")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"  # Apple Silicon
            logger.info("MPS (Apple Silicon) available")
        else:
            device = "cpu"
            logger.info("Using CPU for inference")
        
        return device
    
    def get_llm_model(self, model_name: str = "meta-llama/Llama-3.1-8B-Instruct") -> Dict[str, Any]:
        """Load and return the LLM model and tokenizer"""
        
        if 'llm' in self._models:
            return self._models['llm']
        
        try:
            logger.info(f"Loading LLM model: {model_name}")
            
            # Import here to avoid loading dependencies unless needed
            from transformers import (
                AutoTokenizer, 
                AutoModelForCausalLM,
                BitsAndBytesConfig
            )
            
            # Configure quantization for memory efficiency
            if self._device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            else:
                quantization_config = None
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self._model_cache_dir,
                trust_remote_code=True
            )
            
            # Set pad token if not exists
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=self._model_cache_dir,
                quantization_config=quantization_config,
                device_map="auto" if self._device == "cuda" else None,
                torch_dtype=torch.float16 if self._device in ["cuda", "mps"] else torch.float32,
                trust_remote_code=True
            )
            
            if self._device != "cuda":
                model = model.to(self._device)
            
            # Set to eval mode
            model.eval()
            
            self._models['llm'] = {
                'model': model,
                'tokenizer': tokenizer,
                'device': self._device,
                'model_name': model_name
            }
            
            logger.info(f"LLM model loaded successfully on {self._device}")
            return self._models['llm']
            
        except Exception as e:
            logger.error(f"Failed to load LLM model: {str(e)}")
            raise
    
    def get_asr_model(self, model_size: str = "large-v3") -> Dict[str, Any]:
        """Load and return the ASR (Whisper) model"""
        
        if 'asr' in self._models:
            return self._models['asr']
        
        try:
            logger.info(f"Loading ASR model: faster-whisper {model_size}")
            
            # Import here to avoid loading dependencies unless needed
            from faster_whisper import WhisperModel
            
            # Determine device for faster-whisper
            if self._device == "cuda":
                device = "cuda"
                compute_type = "float16"
            else:
                device = "cpu"
                compute_type = "int8"
            
            # Load faster-whisper model
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(self._model_cache_dir)
            )
            
            self._models['asr'] = {
                'model': model,
                'device': device,
                'compute_type': compute_type,
                'model_size': model_size
            }
            
            logger.info(f"ASR model loaded successfully on {device}")
            return self._models['asr']
            
        except Exception as e:
            logger.error(f"Failed to load ASR model: {str(e)}")
            raise
    
    def unload_model(self, model_type: str):
        """Unload a specific model to free memory"""
        
        if model_type in self._models:
            logger.info(f"Unloading {model_type} model")
            
            if model_type == 'llm' and 'model' in self._models[model_type]:
                # Clear CUDA cache if using GPU
                if self._device == "cuda":
                    torch.cuda.empty_cache()
                del self._models[model_type]['model']
                del self._models[model_type]['tokenizer']
            
            elif model_type == 'asr' and 'model' in self._models[model_type]:
                del self._models[model_type]['model']
            
            del self._models[model_type]
            logger.info(f"{model_type} model unloaded")
    
    def unload_all_models(self):
        """Unload all models to free memory"""
        
        for model_type in list(self._models.keys()):
            self.unload_model(model_type)
        
        # Clear CUDA cache
        if self._device == "cuda":
            torch.cuda.empty_cache()
        
        logger.info("All models unloaded")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        
        stats = {
            'device': self._device,
            'models_loaded': list(self._models.keys())
        }
        
        if self._device == "cuda" and torch.cuda.is_available():
            stats.update({
                'cuda_memory_allocated': torch.cuda.memory_allocated() / 1024**3,  # GB
                'cuda_memory_reserved': torch.cuda.memory_reserved() / 1024**3,   # GB
                'cuda_memory_free': (torch.cuda.get_device_properties(0).total_memory - 
                                    torch.cuda.memory_reserved()) / 1024**3        # GB
            })
        
        return stats
    
    def is_model_loaded(self, model_type: str) -> bool:
        """Check if a specific model is loaded"""
        return model_type in self._models
    
    @property
    def device(self) -> str:
        """Get the current device"""
        return self._device
    
    @property
    def model_cache_dir(self) -> Path:
        """Get the model cache directory"""
        return self._model_cache_dir 