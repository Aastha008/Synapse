import uvicorn
import config

if __name__ == '__main__':
    host = getattr(config, 'API_HOST', '0.0.0.0')
    port = getattr(config, 'API_PORT', 8000)
    uvicorn.run(
        'api.main:app',
        host=host,
        port=port,
        reload=False,
        log_level='info',
    )
