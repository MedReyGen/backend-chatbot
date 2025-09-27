from flask import Flask, request, jsonify, Response
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import logging
from flask_cors import CORS

# Setup logging untuk production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)

# Enable CORS untuk production
CORS(app, origins=["*"])  # Sesuaikan dengan domain frontend Anda

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

# System prompt untuk chatbot medis
SYSTEM_PROMPT = """Anda adalah asisten virtual dalam memberikan informasi, saran medis awal, dan panduan lanjutan kepada pengguna untuk penyakit pernafasan seperti pneumonia, tuberkulosis (TBC), dan COVID-19. Tidak bisa menjawab penyakit lainnya."""

@app.route('/generate-stream', methods=['POST'])
def generate_stream():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
            
        user_message = data.get('message', '')
        
        if not user_message or user_message.strip() == '':
            return jsonify({'error': 'Message is required'}), 400
        
        # Log request untuk monitoring
        logger.info(f"Received message: {user_message[:100]}...")
        
        def generate():
            try:
                stream = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V3.1-Terminus:novita",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    stream=True,
                    max_tokens=3000,
                    temperature=0.88,
                    top_p=1,
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
                
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                yield f"data: {json.dumps({'error': 'Internal server error'})}\n\n"
        
        return Response(
            generate(), 
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in generate_stream: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': os.environ.get('TIMESTAMP', 'unknown')
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)