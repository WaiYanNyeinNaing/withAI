from __future__ import annotations

import os
from typing import Any, Callable, List, Optional, Dict
from google import genai
from google.genai import types

class SimpleAgent:
    """
    A simple agent wrapper around google-genai Client.
    """
    def __init__(
        self,
        name: str,
        model: str,
        instruction: str,
        tools: Optional[List[Callable[..., Any]]] = None,
        generate_content_config: Optional[types.GenerateContentConfig] = None,
    ):
        self.name = name
        self.model = model
        self.instruction = instruction
        self.tools = tools or []
        self.config = generate_content_config or types.GenerateContentConfig()
        
        # Initialize client
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def _func_to_tool(self, func: Callable) -> types.FunctionDeclaration:
        """
        Convert a Python function to a FunctionDeclaration.
        This is a simplified conversion.
        """
        import inspect
        
        name = func.__name__
        doc = func.__doc__ or ""
        sig = inspect.signature(func)
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            # Map python types to JSON schema types
            p_type = "STRING" # Default
            if param.annotation == int:
                p_type = "INTEGER"
            elif param.annotation == float:
                p_type = "NUMBER"
            elif param.annotation == bool:
                p_type = "BOOLEAN"
            elif param.annotation == list or param.annotation == List:
                p_type = "ARRAY"
            elif param.annotation == dict or param.annotation == Dict:
                p_type = "OBJECT"
                
            properties[param_name] = {"type": p_type}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
        return types.FunctionDeclaration(
            name=name,
            description=doc,
            parameters={
                "type": "OBJECT",
                "properties": properties,
                "required": required
            }
        )

    def generate_content(
        self,
        contents: str,
        tools: Optional[List[Callable[..., Any]]] = None,
    ) -> Any:
        """
        Generate content using the model.
        """
        # Merge tools
        current_tools = (self.tools or []) + (tools or [])
        
        config = self.config
        
        if current_tools:
            # Convert python functions to FunctionDeclarations
            fds = [self._func_to_tool(f) for f in current_tools]
            config.tools = [types.Tool(function_declarations=fds)]
        
        return self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
