"""
Prompt template for LLM interactions.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from string import Formatter

logger = logging.getLogger(__name__)

class PromptTemplate:
    """
    Template for LLM prompts with variable substitution.
    
    This class provides functionality for:
    1. Creating reusable prompt templates
    2. Variable substitution in templates
    3. Conditional sections in templates
    4. Formatting and validation
    """
    
    def __init__(
        self,
        template: str,
        required_variables: Optional[List[str]] = None,
        default_values: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the prompt template.
        
        Args:
            template: Template string with variables in {variable_name} format
            required_variables: List of variables that must be provided
            default_values: Default values for variables
        """
        self.template = template
        self.default_values = default_values or {}
        
        # Extract all variables from the template
        self.variables = self._extract_variables()
        
        # Set required variables
        if required_variables:
            self.required_variables = required_variables
        else:
            # By default, all variables without default values are required
            self.required_variables = [
                var for var in self.variables 
                if var not in self.default_values
            ]
    
    def format(self, **kwargs) -> str:
        """
        Format the template with the provided variables.
        
        Args:
            **kwargs: Variables to substitute in the template
            
        Returns:
            Formatted prompt
            
        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing required variables
        missing_vars = [
            var for var in self.required_variables 
            if var not in kwargs and var not in self.default_values
        ]
        
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        # Combine default values with provided values
        values = {**self.default_values, **kwargs}
        
        # Process conditional sections
        processed_template = self._process_conditionals(self.template, values)
        
        # Format the template
        try:
            return processed_template.format(**values)
        except KeyError as e:
            logger.error(f"Missing variable in template: {e}")
            raise ValueError(f"Missing variable in template: {e}")
    
    def _extract_variables(self) -> List[str]:
        """
        Extract all variables from the template.
        
        Returns:
            List of variable names
        """
        # Use string.Formatter to extract field names
        formatter = Formatter()
        return [
            field_name for _, field_name, _, _ in formatter.parse(self.template)
            if field_name is not None
        ]
    
    def _process_conditionals(self, template: str, values: Dict[str, Any]) -> str:
        """
        Process conditional sections in the template.
        
        Conditional sections have the format:
        {%if variable_name%}content if variable exists and is truthy{%endif%}
        {%if variable_name%}content if truthy{%else%}content if falsy{%endif%}
        
        Args:
            template: Template string
            values: Variable values
            
        Returns:
            Processed template with conditionals resolved
        """
        # Process if-else conditionals
        pattern = r'\{%if\s+([^%]+)%\}(.*?)(?:\{%else%\}(.*?))?\{%endif%\}'
        
        def replace_conditional(match):
            condition_var = match.group(1).strip()
            if_content = match.group(2)
            else_content = match.group(3) or ''
            
            # Check if the condition variable exists and is truthy
            if condition_var in values and values[condition_var]:
                return if_content
            else:
                return else_content
        
        # Replace all conditionals
        processed = re.sub(pattern, replace_conditional, template, flags=re.DOTALL)
        return processed
    
    @classmethod
    def from_file(cls, file_path: str, **kwargs) -> 'PromptTemplate':
        """
        Create a prompt template from a file.
        
        Args:
            file_path: Path to the template file
            **kwargs: Additional arguments for PromptTemplate constructor
            
        Returns:
            PromptTemplate instance
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        return cls(template, **kwargs)
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save the template to a file.
        
        Args:
            file_path: Path to save the template to
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.template)
