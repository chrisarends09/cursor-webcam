from flask import Blueprint, jsonify, render_template, redirect, url_for
from flask_swagger_ui import get_swaggerui_blueprint

# Configure Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Webcam Manager API"
    }
)

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/api/swagger.json')
def swagger_spec():
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "Webcam Manager API",
            "description": "API for managing webcam snapshots",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "/"
            }
        ],
        "paths": {
            "/api/webcams": {
                "get": {
                    "summary": "Get all available webcams",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "List of webcams",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/Webcam"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/webcams/user": {
                "get": {
                    "summary": "Get user's configured webcams",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "List of user's webcams",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/UserWebcam"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/token": {
                "post": {
                    "summary": "Get API token",
                    "security": [{"SessionAuth": []}],
                    "responses": {
                        "200": {
                            "description": "API token",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "token": {"type": "string"},
                                            "expires_in": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/system/status": {
                "get": {
                    "summary": "Get system status",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "System status information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SystemStatus"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/system/snapshots": {
                "get": {
                    "summary": "Get snapshot statistics",
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Snapshot statistics",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SnapshotStats"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Webcam": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "url": {"type": "string"},
                        "type": {"type": "string"},
                        "resort": {"type": "string"}
                    }
                },
                "UserWebcam": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "interval_hours": {"type": "integer"},
                        "last_capture": {"type": "string", "format": "date-time"},
                        "next_capture": {"type": "string", "format": "date-time"}
                    }
                },
                "SystemStatus": {
                    "type": "object",
                    "properties": {
                        "system": {
                            "type": "object",
                            "properties": {
                                "cpu_percent": {"type": "number"},
                                "memory": {
                                    "type": "object",
                                    "properties": {
                                        "total": {"type": "integer"},
                                        "available": {"type": "integer"},
                                        "percent": {"type": "number"}
                                    }
                                },
                                "disk": {
                                    "type": "object",
                                    "properties": {
                                        "total": {"type": "integer"},
                                        "free": {"type": "integer"},
                                        "percent": {"type": "number"}
                                    }
                                }
                            }
                        },
                        "application": {
                            "type": "object",
                            "properties": {
                                "snapshots": {
                                    "type": "object",
                                    "properties": {
                                        "count": {"type": "integer"},
                                        "size": {"type": "integer"}
                                    }
                                },
                                "users": {
                                    "type": "object",
                                    "properties": {
                                        "total": {"type": "integer"},
                                        "active": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer"
                },
                "SessionAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session"
                }
            }
        }
    }) 

@docs_bp.route('/api/docs/postman')
def postman_collection():
    """Generate Postman collection for the API"""
    swagger = swagger_spec().json
    
    collection = {
        "info": {
            "name": "Webcam Manager API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    # Convert paths to Postman format
    for path, methods in swagger['paths'].items():
        for method, details in methods.items():
            collection['item'].append({
                "name": details['summary'],
                "request": {
                    "method": method.upper(),
                    "url": {
                        "raw": "{{baseUrl}}" + path,
                        "host": ["{{baseUrl}}"],
                        "path": path.split('/')[1:]
                    },
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ] if method in ['post', 'put'] else []
                }
            })
    
    return jsonify(collection) 

@docs_bp.route('/api')
def api_docs():
    """Show API documentation page"""
    return render_template('docs/api.html')

@docs_bp.route('/api/docs')
def swagger_ui():
    """Redirect to Swagger UI"""
    return redirect(url_for('swagger_ui.show')) 