from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv
from position_analyzer import PositionAnalyzer
from concepts_repository import ConceptsRepository

app = Flask(__name__)

load_dotenv()

allowed_ip = os.getenv('ALLOWED_IP', '127.0.0.1')
cors = CORS(app, resources={r"/*": {"origins": f"http://{allowed_ip}"}})

stockfish_path = os.getenv('STOCKFISH_PATH')
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
chatgpt_version = os.getenv('CHATGPT_VERSION')
use_rag = os.getenv('USE_RAG', 'False').lower() == 'true'

analyzer = PositionAnalyzer(stockfish_path)
repository = ConceptsRepository() if use_rag else None
@app.route('/analyze', methods=['GET'])
def analyze():    
    aspect = request.args.get('aspect')
    fen = request.args.get('fen')

    try:
        if not aspect or not fen:
            return jsonify({'error': 'Not enough parameters. question and fen are required'}), 400

        if aspect not in ['General analysis', 'Material', 'Pawn structure', 'King\'s safety',
                        'Piece activity', 'Threats', 'Space', 'Plans']:
            return jsonify({'error': 'Wrong value for aspect parameter'}), 400
        
        if analyzer.is_initial_position(fen):
            return jsonify({'answer': 'Please, set a position on the board'})
        
        pre_analysis = analyzer.analyze(fen)
        if(pre_analysis == ''):
            return jsonify({'answer': default_no_analysis_answer()})

        phase = analyzer.compute_game_phase(fen)
        keywords = extract_keywords(pre_analysis, aspect)
        concepts = repository.search(phase, aspect, keywords) if use_rag else None
        prompt = build_prompt(aspect, fen, pre_analysis, concepts)
                
        response = ask_chatgpt(prompt)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'An internal server error has occurred. Please try again later.'}), 500

def build_prompt(aspect, fen, pre_analysis, concepts):
    piece_locations = analyzer.get_piece_locations(fen)
    prompt = (
            f"Piece Locations:\n{piece_locations}\n"
            f"Pre-analysis:\n{get_relevant_pre_analysis(pre_analysis, aspect)}\n\n"
            f'Use markdown format on response.\n'
            f'Don\'t include any board representation.\n'
            f'Don\'t include references to the raw report.\n'
            f'Don\'t include number of controlled squares, generalize.\n'
            f'Use a maximum of {500 if aspect == 'General analysis'else 200} words\n'
            f'Includes explanations of the key concepts included in the analysis\n\n'
            f"Question: {build_question(aspect)}\n\n")

    if use_rag and concepts != '':
        prompt += (
            f'Theese are a list of relevant concepts '
            f'that you can use as context:\n{concepts}')
        
    return prompt

def default_no_analysis_answer():
    return (f'The present position has a clear advantage '
            f'of one player over the other to be analyzed from a strategic perspective. '
            f'Pay attention to the tactical keys and try to solve it by yourself.')

def build_question(aspect):
    if aspect == 'General analysis':
        return 'Make a complete analysis of the position.'
    elif aspect == 'Plans':
        return 'Make an analysis of possible plans on the position.'
    else:
        return f'Make an analysis of the {aspect} of the position.'

def ask_chatgpt(prompt):
    response = client.chat.completions.create(
        model=chatgpt_version,
        messages=[
            {"role": "system", "content": "You are a helpful chess assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    return jsonify({'answer': answer})

def extract_keywords(pre_analysis, aspect):
    pre_analysis = get_relevant_pre_analysis(pre_analysis, aspect)
    if isinstance(pre_analysis, dict):
        text_content = " ".join(str(value) for value in pre_analysis.values())
    else:
        text_content = str(pre_analysis)

    prompt = (f'This is a raw analysis of a chess position\n'
              f'Extract a set of 5 key concepts of it.\n'
              f'The keywords should be write in only one line, splits by comas.\n\n'
              f'{text_content}')
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    return answer.split(',')

def get_relevant_pre_analysis(pre_analysis, aspect):
    match aspect:
        case 'Material':
            return pre_analysis['Material']
        case 'Pawn structure':
            return pre_analysis['Pawn Structure']
        case 'King\'s safety':
            return pre_analysis['King Safety']
        case 'Piece activity':
            return pre_analysis['Pieces Activity']
        case 'Threats':
            return pre_analysis['Threads']
        case 'Space':
            return pre_analysis['Space']
        case _:
            return pre_analysis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)