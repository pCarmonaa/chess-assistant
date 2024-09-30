import subprocess
import re
import chess

class PositionAnalyzer:
    def __init__(self, stockfish_path):
        self.stockfish_path = stockfish_path

    def is_initial_position(self, fen):
        return fen.split(' ')[0] == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'

    def get_piece_locations(self, fen):
        """
        Returns the location of each piece on the board based on the FEN string.
        Pieces are listed first for White, then for Black.
        """
        board = chess.Board(fen)
        piece_locations = {}

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_type = piece.piece_type
                piece_color = 'White' if piece.color == chess.WHITE else 'Black'
                piece_name = chess.PIECE_NAMES[piece_type].capitalize()  # Gets piece name like 'pawn', 'knight', etc.
                square_name = chess.square_name(square)
                piece_locations[square_name] = f'{piece_color} {piece_name}'

        sorted_piece_locations = dict(sorted(piece_locations.items(), key=lambda x: (x[1].split()[0] == 'Black', x[0])))

        return sorted_piece_locations
    
    def analyze(self, fen):
        """
        Returns a raw position analysis powered by Stockfish.
        """
        process = subprocess.Popen(
            [self.stockfish_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        commands = f"position fen {fen}\neval\n"
        stdout, stderr = process.communicate(input=commands)

        if self.has_no_analysis(stdout):
            return ""

        if stderr:
            raise Exception(f"Error running Stockfish: {stderr}")

        try:
            raw_info = stdout.split('Begin position analysis.')[1].split('End position analysis.')[0]
        except IndexError:
            raise Exception("Error processing Stockfish output: expected traces not found in output.")

        return self.parse_evaluation(raw_info, fen)
    
    def has_no_analysis(self, stdout):
        return ("Material:" not in stdout or
            "Pawn structure:" not in stdout or
            "Pieces activity:" not in stdout or
            "King safety:" not in stdout or
            "Trheats:" not in stdout or
            "Space:" not in stdout)

    def parse_evaluation(self, raw_info, fen):
        parsed_info = {}

        parsed_info['Material'] = self.parse_material(raw_info)
        parsed_info['Pawn Structure'] = self.parse_pawn_structure(raw_info)
        parsed_info['King Safety'] = self.parse_king_safety(raw_info, fen)
        parsed_info['Pieces Activity'] = self.parse_pieces_activity(raw_info)
        parsed_info['Threads'] = self.parse_threads(raw_info, parsed_info['King Safety'])
        parsed_info['Space'] = self.parse_space(raw_info)

        return parsed_info
    
    def parse_material(self, raw_info):
        try:
            material_info = {}

            def extract_material_section(section_name, raw_info):
                pattern = (
                    fr'{section_name}:[\s\S]*?Pawns: (\d+)[\s\S]*?Bishops: (\d+)[\s\S]*?'
                    fr'Bishops pair:(true|false)[\s\S]*?Knight: (\d+)[\s\S]*?Rooks: (\d+)[\s\S]*?'
                    fr'Queens: (\d+)'
                )
                material_section = re.findall(pattern, raw_info)
                if material_section:
                    return {
                        'Pawns': int(material_section[0][0]),
                        'Bishops': int(material_section[0][1]),
                        'Bishops pair': material_section[0][2] == 'true',
                        'Knights': int(material_section[0][3]),
                        'Rooks': int(material_section[0][4]),
                        'Queens': int(material_section[0][5])
                    }
                return None

            material_info['White material'] = extract_material_section('White matetial', raw_info)
            material_info['Black material'] = extract_material_section('Black matetial', raw_info)

            return material_info
        except:
            return {}

    def parse_pawn_structure(self, raw_info):
        try:
            white_pawn_structure = raw_info.split('Pawn structure of White')[1]\
                                        .split('Pawn structure of Black')[0]
            black_pawn_structure = raw_info.split('Pawn structure of Black')[1]\
                                        .split('Pieces activity')[0]
            
            # Extract positions of white and black pawns
            white_pawns = re.findall(r'Pawn of (\w\d+)', white_pawn_structure)
            black_pawns = re.findall(r'Pawn of (\w\d+)', black_pawn_structure)

            white_passed_pawns = self.calculate_passed_pawns(
                white_pawns, black_pawns, raw_info, is_white=True
            )
            black_passed_pawns = self.calculate_passed_pawns(
                black_pawns, white_pawns, raw_info, is_white=False
            )

            white_backward_pawns = self.extract_backward_pawns(white_pawn_structure)
            black_backward_pawns = self.extract_backward_pawns(black_pawn_structure)

            white_phalanx_pawns = self.calculate_phalanx(white_pawn_structure)
            black_phalanx_pawns = self.calculate_phalanx(black_pawn_structure)

            white_isolated_pawns = self.calculate_isolated_pawns(white_pawns)
            black_isolated_pawns = self.calculate_isolated_pawns(black_pawns)

            white_islands = self.calculate_pawn_islands(white_pawn_structure)
            black_islands = self.calculate_pawn_islands(black_pawn_structure)

            pawn_structure = {
                'White Passed Pawns': white_passed_pawns,
                'Black Passed Pawns': black_passed_pawns,
                'White Backward Pawns': white_backward_pawns,
                'Black Backward Pawns': black_backward_pawns,
                'White Isolated Pawns': white_isolated_pawns,
                'Black Isolated Pawns': black_isolated_pawns,
                'White Pawn Islands': white_islands,
                'Black Pawn Islands': black_islands,
                'White Phalanx Pawns': white_phalanx_pawns,
                'Black Phalanx Pawns': black_phalanx_pawns
            }

            return pawn_structure
        except:
            return {}

    def calculate_passed_pawns(self, own_pawns, opposing_pawns, raw_info, is_white):
        def is_passed_pawn(pawn, opposing_pawns, is_white):
            column, rank = pawn[0], int(pawn[1])
            column_number = ord(column) - ord('a')
            
            for opp_pawn in opposing_pawns:
                opp_column, opp_rank = opp_pawn[0], int(opp_pawn[1])
                opp_column_number = ord(opp_column) - ord('a')
                
                if abs(column_number - opp_column_number) <= 1:
                    if is_white:
                        if opp_rank > rank:
                            return False
                    else:
                        if opp_rank < rank:
                            return False
            return True

        def extract_passed_pawn_info(pawn, passed_pawn_section):
            passed_pawn_info = {}
            pawn_regex = fr'Passed pawn of {pawn} square:[\s\S]*?(\n\n|\Z)'
            match = re.search(pawn_regex, passed_pawn_section)
            if match:
                info = match.group(0)
                passed_pawn_info['Squares to Promotion'] = re.findall(
                    r'Is at (\d+) squares of promotion', info)
                passed_pawn_info['Enemy King Distance'] = re.findall(
                    r'The king enemy is at (\d+) squares of distance of it', info)
                passed_pawn_info['Blocked Status'] = re.findall(
                    r'(Is blocked and can not advance|Is not blocked and free to advance)', 
                    info)
            return passed_pawn_info if passed_pawn_info else None

        passed_pawns = [pawn for pawn in own_pawns if 
                        is_passed_pawn(pawn, opposing_pawns, is_white)]

        # Extract passed pawn section from raw_info
        color = 'White' if is_white else 'Black'
        passed_pawn_section = re.findall(
            rf'Passed pawns of {color}:[\s\S]*?(?=Passed pawns of |$)', raw_info
        )

        passed_pawn_info = {
            pawn: extract_passed_pawn_info(pawn, passed_pawn_section[0])
            for pawn in passed_pawns if passed_pawn_section
        }

        passed_pawn_final = {
            pawn: passed_pawn_info.get(pawn, {}) for pawn in passed_pawns
        }

        return passed_pawn_final

    def extract_backward_pawns(self, pawn_structure):
        backward_pawns = re.findall(
            r'Pawn of (\w\d) square:\n(?:[^\n]*\n){1,6}\s*Is a backward pawn: true',
            pawn_structure, re.DOTALL
        )
        return backward_pawns

    def calculate_pawn_islands(self, pawn_structure):
        pawns = re.findall(r'Pawn of (\w\d+)', pawn_structure)
        pawns_by_column = {}
        for pawn in pawns:
            column = pawn[0]
            if column in pawns_by_column:
                pawns_by_column[column].append(pawn)
            else:
                pawns_by_column[column] = [pawn]
        
        sorted_columns = sorted(pawns_by_column.keys())
        islands = []
        current_island = []

        for i in range(len(sorted_columns)):
            if i == 0:
                current_island.extend(pawns_by_column[sorted_columns[i]])
            elif ord(sorted_columns[i]) == ord(sorted_columns[i - 1]) + 1:
                current_island.extend(pawns_by_column[sorted_columns[i]])
            else:
                islands.append(current_island)
                current_island = pawns_by_column[sorted_columns[i]]
        
        if current_island:
            islands.append(current_island)

        return islands

    def calculate_phalanx(self, pawn_structure):
        pawns = re.findall(r'Pawn of (\w\d+)', pawn_structure)

        pawns_by_row = {}
        for pawn in pawns:
            row = pawn[1]
            if row in pawns_by_row:
                pawns_by_row[row].append(pawn)
            else:
                pawns_by_row[row] = [pawn]

        phalanxes = []

        for row, pawns_in_row in pawns_by_row.items():
            sorted_pawns = sorted(pawns_in_row)
            current_phalanx = [sorted_pawns[0]]

            for i in range(1, len(sorted_pawns)):
                if ord(sorted_pawns[i][0]) == ord(sorted_pawns[i - 1][0]) + 1:
                    current_phalanx.append(sorted_pawns[i])
                else:
                    if len(current_phalanx) > 1:
                        phalanxes.append(current_phalanx)
                    current_phalanx = [sorted_pawns[i]]
            
            if len(current_phalanx) > 1:
                phalanxes.append(current_phalanx)

        return phalanxes

    def calculate_isolated_pawns(self, pawns):
        isolated_pawns = []
        columns_with_pawn = [ord(pawn[0]) for pawn in pawns]
        
        for pawn in pawns:
            if ord(pawn[0])-1 not in columns_with_pawn and ord(pawn[0])+1 not in columns_with_pawn:
                isolated_pawns.append(pawn)

        return isolated_pawns

    def parse_king_safety(self, raw_info, fen):
        # Capture squares attacked, attacked twice, and defended on the white king's flank
        white_attacks = re.findall(
            r'White King safety[\s\S]*?Squares attacked at King flank:\s*([A-H][1-8]'
            r'(?:, [A-H][1-8])*)', raw_info
        )
        white_double_attacks = re.findall(
            r'White King safety[\s\S]*?Squares attacked twice at King flank:\s*([A-H]'
            r'[1-8](?:, [A-H][1-8])*)', raw_info
        )
        white_defended_squares = re.findall(
            r'White King safety[\s\S]*?Squares defended at King flank:\s*([A-H][1-8]'
            r'(?:, [A-H][1-8])*)', raw_info
        )

        # Capture possible checks available for white pieces
        white_bishop_checks = re.findall(
            r'White King safety[\s\S]*?Bishop checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )
        white_knight_checks = re.findall(
            r'White King safety[\s\S]*?Knight checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )
        white_rook_checks = re.findall(
            r'White King safety[\s\S]*?Rook checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )
        white_queen_checks = re.findall(
            r'White King safety[\s\S]*?Queen checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )

        # Capture squares attacked, attacked twice, and defended on the black king's flank
        black_attacks = re.findall(
            r'Black King safety[\s\S]*?Squares attacked at King flank:\s*([A-H][1-8]'
            r'(?:, [A-H][1-8])*)', raw_info
        )
        black_double_attacks = re.findall(
            r'Black King safety[\s\S]*?Squares attacked twice at King flank:\s*([A-H]'
            r'[1-8](?:, [A-H][1-8])*)', raw_info
        )
        black_defended_squares = re.findall(
            r'Black King safety[\s\S]*?Squares defended at King flank:\s*([A-H][1-8]'
            r'(?:, [A-H][1-8])*)', raw_info
        )

        # Capture possible checks available for black pieces
        black_bishop_checks = re.findall(
            r'Black King safety[\s\S]*?Bishop checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )
        black_knight_checks = re.findall(
            r'Black King safety[\s\S]*?Knight checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )
        black_rook_checks = re.findall(
            r'Black King safety[\s\S]*?Rook checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )
        black_queen_checks = re.findall(
            r'Black King safety[\s\S]*?Queen checks availables:\s*([A-H][1-8](?:, '
            r'[A-H][1-8])*)', raw_info
        )

        num_white_attacks = len(white_attacks[0].split(', ')) if white_attacks else 0
        num_white_double_attacks = len(white_double_attacks[0].split(', ')) if \
            white_double_attacks else 0
        num_white_defended_squares = len(white_defended_squares[0].split(', ')) if \
            white_defended_squares else 0
        num_black_attacks = len(black_attacks[0].split(', ')) if black_attacks else 0
        num_black_double_attacks = len(black_double_attacks[0].split(', ')) if \
            black_double_attacks else 0
        num_black_defended_squares = len(black_defended_squares[0].split(', ')) if \
            black_defended_squares else 0

        king_safety = {
            'White King Safety': {
                'Attacked Squares': num_white_attacks,
                'Double Attacked Squares': num_white_double_attacks,
                'Defended Squares': num_white_defended_squares,
                'Bishop Checks': white_bishop_checks[0] if white_bishop_checks else 'None',
                'Knight Checks': white_knight_checks[0] if white_knight_checks else 'None',
                'Rook Checks': white_rook_checks[0] if white_rook_checks else 'None',
                'Queen Checks': white_queen_checks[0] if white_queen_checks else 'None'
            },
            'Black King Safety': {
                'Attacked Squares': num_black_attacks,
                'Double Attacked Squares': num_black_double_attacks,
                'Defended Squares': num_black_defended_squares,
                'Bishop Checks': black_bishop_checks[0] if black_bishop_checks else 'None',
                'Knight Checks': black_knight_checks[0] if black_knight_checks else 'None',
                'Rook Checks': black_rook_checks[0] if black_rook_checks else 'None',
                'Queen Checks': black_queen_checks[0] if black_queen_checks else 'None'
            }
        }

        return king_safety

    def parse_pieces_activity(self, raw_info):
        try:
            pieces_activity = {
                'White pieces activity': [],
                'Black pieces activity': []
            }

            # Find all blocks that describe each piece's activity
            pieces_data = re.findall(
                r'(\w+ \w+ of square \w\d[\s\S]*?(?=\n\w+ \w+ of square|\n\n|\Z))',
                raw_info
            )

            # Create a dictionary with the piece scores extracted from the NNUE pieces score section
            nnue_scores = re.findall(
                r'(\w+ \w+) of (\w\d): ([\d.]+)',
                raw_info
            )
            piece_scores = {
                f'{name} of {square}': float(score)
                for name, square, score in nnue_scores
            }

            for piece_data in pieces_data:
                # Identify the type of piece and its position
                piece_type = re.findall(
                    r'(\w+ \w+) of square (\w\d)',
                    piece_data
                )
                if not piece_type:
                    continue
                
                piece_name, piece_position = piece_type[0]
                piece_info = []

                # Extract the number of squares controlled
                controlled_squares = re.findall(
                    r'Squares controlled by the \w+: ([A-H][1-8](?:, [A-H][1-8])*)',
                    piece_data
                )
                if controlled_squares:
                    num_controlled_squares = len(
                        controlled_squares[0].split(', ')
                    )
                    piece_info.append(
                        f'Controlled squares: {num_controlled_squares}'
                    )

                # Extract the number of squares the piece can move to
                moveable_squares = re.findall(
                    r'The \w+ can move to: (\d+) squares',
                    piece_data
                )
                if moveable_squares:
                    piece_info.append(f'Moveable squares: {moveable_squares[0]}')

                # Extract additional information for specific pieces
                if 'Bishop' in piece_name or 'Knight' in piece_name:
                    distance_from_king = re.findall(
                        r'The \w+ is (\d+) squares far from our king',
                        piece_data
                    )
                    if distance_from_king:
                        piece_info.append(
                            f'Distance from king: {distance_from_king[0]} squares'
                        )

                if 'Bishop' in piece_name:
                    same_color_pawns = re.findall(
                        r'Pawns on the same bishop color squared: (\d+)',
                        piece_data
                    )
                    if same_color_pawns:
                        piece_info.append(
                            f'Pawns on same color squared: {same_color_pawns[0]}'
                        )
                    
                    x_rayed_pawns = re.findall(
                        r'Number of enemy pawns x-rayed: (\d+)',
                        piece_data
                    )
                    if x_rayed_pawns:
                        piece_info.append(f'Enemy pawns x-rayed: {x_rayed_pawns[0]}')
                    
                    long_diagonal = re.findall(
                        r'The bishop is on a long diagonal and can see both center squares\.',
                        piece_data
                    )
                    if long_diagonal:
                        piece_info.append(
                            'On long diagonal, sees both center squares'
                        )

                if 'Rook' in piece_name:
                    open_column = re.findall(
                        r'The rook is on \(semi-\)open column\.',
                        piece_data
                    )
                    if open_column:
                        piece_info.append('On (semi-)open column')

                if 'Queen' in piece_name:
                    pin_or_discover_attack = re.findall(
                        r'Exists pin in or discover attack over de queen\.',
                        piece_data
                    )
                    if pin_or_discover_attack:
                        piece_info.append('Pin or discovered attack exists')

                piece_key = f'{piece_name} of {piece_position}'
                piece_activity = {
                    'Piece': piece_key,
                    'Piece info': piece_info,
                    'Piece score': piece_scores.get(piece_key, 'N/A')
                }

                if 'White' in piece_name:
                    pieces_activity['White pieces activity'].append(piece_activity)
                elif 'Black' in piece_name:
                    pieces_activity['Black pieces activity'].append(piece_activity)

            return pieces_activity
        except:
            return {}

    def parse_space(self, raw_info):
        try:
            # Extract the space section for each side
            white_space_section = re.findall(
                r'Space of White:[\s\S]*?Squares behind or at our pawns: '
                r'([A-H][1-8](?:, [A-H][1-8])*)', raw_info
            )
            black_space_section = re.findall(
                r'Space of Black:[\s\S]*?Squares behind or at our pawns: '
                r'([A-H][1-8](?:, [A-H][1-8])*)', raw_info
            )

            white_space_count = len(
                white_space_section[0].split(', ')
            ) if white_space_section else 0
            black_space_count = len(
                black_space_section[0].split(', ')
            ) if black_space_section else 0

            space_info = {
                'White space': white_space_count,
                'Black space': black_space_count
            }

            return space_info
        except:
            return {}

    def parse_threads(self, raw_info, king_safety_info):
        try:
            threads_info = {
                'White threads': {},
                'Black threads': {}
            }

            # Patterns of interest that we want to extract from the report
            patterns = {
                'Enemies could be attacked by knights':
                    r'Enemies atacked by knights: ([A-H][1-8](?:, [A-H][1-8])*)',
                'Enemies could be attacked by Bishops':
                    r'Enemies atacked by Bishops: ([A-H][1-8](?:, [A-H][1-8])*)',
                'Enemies could be attacked by rooks':
                    r'Enemies atacked by rooks: ([A-H][1-8](?:, [A-H][1-8])*)',
                'Enemies could be attacked by Queens':
                    r'Enemies atacked by Queens: ([A-H][1-8](?:, [A-H][1-8])*)',
                'Enemies could be attacked by king':
                    r'Enemies atacked by king: ([A-H][1-8](?:, [A-H][1-8])*)',
                'Squares where our pawns could push on the next move':
                    r'Squares where our pawns can push on the next move:'
                    r'([A-H][1-8](?:, [A-H][1-8])*)'
            }

            # Extract the threats section for each side
            white_threads_section = re.findall(
                r'Threads of White:[\s\S]*?(?=Threads of Black|Trheats|$)',
                raw_info
            )
            black_threads_section = re.findall(
                r'Threads of Black:[\s\S]*?(?=Threads of White|Trheats|$)',
                raw_info
            )

            def extract_info(section, patterns):
                info = {}
                for key, pattern in patterns.items():
                    matches = re.findall(pattern, section)
                    if matches:
                        info[key] = matches[0].split(', ')
                return info

            if white_threads_section:
                threads_info['White threads'] = extract_info(
                    white_threads_section[0], patterns
                )
            if black_threads_section:
                threads_info['Black threads'] = extract_info(
                    black_threads_section[0], patterns
                )

            if 'White King Safety' in king_safety_info:
                white_checks = []
                if king_safety_info['White King Safety'].get('Bishop Checks') and \
                        king_safety_info['White King Safety']['Bishop Checks'] != 'None':
                    white_checks.extend(
                        king_safety_info['White King Safety']['Bishop Checks'].split(', ')
                    )
                if king_safety_info['White King Safety'].get('Knight Checks') and \
                        king_safety_info['White King Safety']['Knight Checks'] != 'None':
                    white_checks.extend(
                        king_safety_info['White King Safety']['Knight Checks'].split(', ')
                    )
                if king_safety_info['White King Safety'].get('Rook Checks') and \
                        king_safety_info['White King Safety']['Rook Checks'] != 'None':
                    white_checks.extend(
                        king_safety_info['White King Safety']['Rook Checks'].split(', ')
                    )
                if king_safety_info['White King Safety'].get('Queen Checks') and \
                        king_safety_info['White King Safety']['Queen Checks'] != 'None':
                    white_checks.extend(
                        king_safety_info['White King Safety']['Queen Checks'].split(', ')
                    )
                if white_checks:
                    threads_info['Black threads']['Possible checks on White King'] = \
                        white_checks

            if 'Black King Safety' in king_safety_info:
                black_checks = []
                if king_safety_info['Black King Safety'].get('Bishop Checks') and \
                        king_safety_info['Black King Safety']['Bishop Checks'] != 'None':
                    black_checks.extend(
                        king_safety_info['Black King Safety']['Bishop Checks'].split(', ')
                    )
                if king_safety_info['Black King Safety'].get('Knight Checks') and \
                        king_safety_info['Black King Safety']['Knight Checks'] != 'None':
                    black_checks.extend(
                        king_safety_info['Black King Safety']['Knight Checks'].split(', ')
                    )
                if king_safety_info['Black King Safety'].get('Rook Checks') and \
                        king_safety_info['Black King Safety']['Rook Checks'] != 'None':
                    black_checks.extend(
                        king_safety_info['Black King Safety']['Rook Checks'].split(', ')
                    )
                if king_safety_info['Black King Safety'].get('Queen Checks') and \
                        king_safety_info['Black King Safety']['Queen Checks'] != 'None':
                    black_checks.extend(
                        king_safety_info['Black King Safety']['Queen Checks'].split(', ')
                    )
                if black_checks:
                    threads_info['White threads']['Possible checks on Black King'] = \
                        black_checks

            return threads_info
        except:
                return {}
        
    def compute_game_phase(self, fen):
        piece_values = {
            'p': 0,
            'n': 1,
            'b': 1,
            'r': 2,
            'q': 4,
            'k': 0,
            'P': 0,
            'N': 1,
            'B': 1,
            'R': 2,
            'Q': 4,
            'K': 0
        }

        parts = fen.split()
        piece_placement = parts[0]
        move_count = int(parts[5])

        total_piece_value = sum(piece_values[piece] for piece in piece_placement if piece in piece_values)
        if total_piece_value < 6:
            return "Endgame"
        elif move_count < 15:
            return "Opening"
        else:
            return "Middlegame"