#!/usr/bin/env python3
"""
Configuration management for AG-UI Streaming MCP Server
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StreamingConfig:
    """Configuration for streaming responses"""
    enabled: bool = True
    chunk_delay_ms: int = 100  # Milliseconds between chunks
    max_chunk_size: int = 3    # Max items per chunk for search results
    progress_indicators: bool = True
    real_time_updates: bool = True
    buffer_size: int = 1024    # Buffer size for streaming


@dataclass
class APIProxyConfig:
    """Configuration for FastAPI proxy"""
    base_url: str = "http://localhost:8000"
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_ms: int = 1000
    connect_timeout: float = 5.0
    read_timeout: float = 30.0
    
    # Authentication
    auth_token: Optional[str] = None
    auth_header_name: str = "Authorization"
    auth_header_prefix: str = "Bearer"
    
    # Request configuration
    follow_redirects: bool = True
    verify_ssl: bool = True
    user_agent: str = "HR-Resume-MCP-Server/1.0"


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Structured logging for production
    structured: bool = False
    json_format: bool = False


@dataclass
class SecurityConfig:
    """Security configuration"""
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    allowed_file_types: List[str] = None
    max_concurrent_requests: int = 10
    
    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = [".pdf", ".doc", ".docx", ".txt"]


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    cache_max_size: int = 1000
    
    # Connection pooling
    max_pool_connections: int = 20
    max_pool_keepalive: int = 5
    keepalive_expiry: float = 30.0
    
    # Request optimization
    enable_compression: bool = True
    enable_http2: bool = True


class MCPServerConfig:
    """Main configuration class for MCP server"""
    
    def __init__(self):
        # Load configuration from environment variables
        self.streaming = StreamingConfig(
            enabled=self._get_bool_env("MCP_STREAMING_ENABLED", True),
            chunk_delay_ms=self._get_int_env("MCP_CHUNK_DELAY_MS", 100),
            max_chunk_size=self._get_int_env("MCP_MAX_CHUNK_SIZE", 3),
            progress_indicators=self._get_bool_env("MCP_PROGRESS_INDICATORS", True),
            real_time_updates=self._get_bool_env("MCP_REAL_TIME_UPDATES", True),
            buffer_size=self._get_int_env("MCP_BUFFER_SIZE", 1024)
        )
        
        self.api_proxy = APIProxyConfig(
            base_url=os.getenv("FASTAPI_BASE_URL", "http://localhost:8000"),
            timeout_seconds=self._get_float_env("MCP_TIMEOUT", 30.0),
            max_retries=self._get_int_env("MCP_MAX_RETRIES", 3),
            retry_delay_ms=self._get_int_env("MCP_RETRY_DELAY_MS", 1000),
            connect_timeout=self._get_float_env("MCP_CONNECT_TIMEOUT", 5.0),
            read_timeout=self._get_float_env("MCP_READ_TIMEOUT", 30.0),
            follow_redirects=self._get_bool_env("MCP_FOLLOW_REDIRECTS", True),
            verify_ssl=self._get_bool_env("MCP_VERIFY_SSL", True),
            user_agent=os.getenv("MCP_USER_AGENT", "HR-Resume-MCP-Server/1.0")
        )
        
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=os.getenv("LOG_FILE"),
            max_bytes=self._get_int_env("LOG_MAX_BYTES", 10 * 1024 * 1024),
            backup_count=self._get_int_env("LOG_BACKUP_COUNT", 5),
            structured=self._get_bool_env("LOG_STRUCTURED", False),
            json_format=self._get_bool_env("LOG_JSON_FORMAT", False)
        )
        
        self.security = SecurityConfig(
            max_request_size=self._get_int_env("MCP_MAX_REQUEST_SIZE", 10 * 1024 * 1024),
            rate_limit_requests=self._get_int_env("MCP_RATE_LIMIT_REQUESTS", 100),
            rate_limit_window_seconds=self._get_int_env("MCP_RATE_LIMIT_WINDOW", 60),
            max_concurrent_requests=self._get_int_env("MCP_MAX_CONCURRENT", 10)
        )
        
        self.performance = PerformanceConfig(
            enable_caching=self._get_bool_env("MCP_ENABLE_CACHING", True),
            cache_ttl_seconds=self._get_int_env("MCP_CACHE_TTL", 300),
            cache_max_size=self._get_int_env("MCP_CACHE_MAX_SIZE", 1000),
            max_pool_connections=self._get_int_env("MCP_MAX_POOL_CONNECTIONS", 20),
            max_pool_keepalive=self._get_int_env("MCP_MAX_POOL_KEEPALIVE", 5),
            keepalive_expiry=self._get_float_env("MCP_KEEPALIVE_EXPIRY", 30.0),
            enable_compression=self._get_bool_env("MCP_ENABLE_COMPRESSION", True),
            enable_http2=self._get_bool_env("MCP_ENABLE_HTTP2", True)
        )
        
        # Server metadata
        self.server_name = "hr-resume-search-streaming"
        self.server_version = "1.0.0"
        self.server_description = "HR Resume Search MCP Server with AG-UI streaming support"
        
        # Validate configuration
        self._validate_config()
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_float_env(self, key: str, default: float) -> float:
        """Get float environment variable"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _validate_config(self):
        """Validate configuration values"""
        # Validate API proxy URL
        if not self.api_proxy.base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid FastAPI base URL: {self.api_proxy.base_url}")
        
        # Validate timeouts
        if self.api_proxy.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.api_proxy.connect_timeout <= 0:
            raise ValueError("Connect timeout must be positive")
        
        # Validate streaming config
        if self.streaming.chunk_delay_ms < 0:
            raise ValueError("Chunk delay must be non-negative")
        
        if self.streaming.max_chunk_size <= 0:
            raise ValueError("Max chunk size must be positive")
        
        # Validate security config
        if self.security.max_request_size <= 0:
            raise ValueError("Max request size must be positive")
        
        if self.security.rate_limit_requests <= 0:
            raise ValueError("Rate limit requests must be positive")
        
        # Validate performance config
        if self.performance.cache_ttl_seconds < 0:
            raise ValueError("Cache TTL must be non-negative")
        
        if self.performance.max_pool_connections <= 0:
            raise ValueError("Max pool connections must be positive")
    
    def set_auth_token(self, token: str):
        """Set authentication token for API requests"""
        self.api_proxy.auth_token = token
    
    def clear_auth_token(self):
        """Clear authentication token"""
        self.api_proxy.auth_token = None
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.api_proxy.user_agent
        }
        
        if self.api_proxy.auth_token:
            headers[self.api_proxy.auth_header_name] = (
                f"{self.api_proxy.auth_header_prefix} {self.api_proxy.auth_token}"
            )
        
        return headers
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "server": {
                "name": self.server_name,
                "version": self.server_version,
                "description": self.server_description
            },
            "streaming": self.streaming.__dict__,
            "api_proxy": {
                k: v for k, v in self.api_proxy.__dict__.items() 
                if k != "auth_token"  # Don't expose token
            },
            "logging": self.logging.__dict__,
            "security": self.security.__dict__,
            "performance": self.performance.__dict__
        }
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"MCPServerConfig(server={self.server_name}, api_url={self.api_proxy.base_url})"


# Global configuration instance
config = MCPServerConfig()


def get_config() -> MCPServerConfig:
    """Get global configuration instance"""
    return config


def reload_config() -> MCPServerConfig:
    """Reload configuration from environment"""
    global config
    config = MCPServerConfig()
    return config