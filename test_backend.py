import unittest
from unittest.mock import patch
import numpy as np
from backend import main as backend_main
from backend.motor_estrategico import find_best_move_guardian, find_best_move_intruder, evaluate_state
from backend.vision_module import VisionSystem

class TestStrategicEngine(unittest.TestCase):
    def setUp(self):
        # Create a simple mock grid 5x5
        self.grid_map = []
        for y in range(1, 6):
            for x in range(1, 6):
                # 1 is shelf, 0 is path
                if y in (1, 3, 5) and x in (1, 3, 5):
                    self.grid_map.append({'x': x, 'y': y, 'val': 1})
                else:
                    self.grid_map.append({'x': x, 'y': y, 'val': 0})
        self.weights = {'w1': 5.0, 'w2': 15.0, 'w3': 10.0}

    def test_heuristic_calculation(self):
        # Guardian closer to intruder should have higher heuristic value
        v_close = evaluate_state((3, 4), (3, 5), self.grid_map, self.weights)
        v_far = evaluate_state((1, 2), (5, 4), self.grid_map, self.weights)
        self.assertGreater(v_close, v_far)

    def test_minimax_decisions(self):
        # Guardian pos (3,5), Intruder pos (2,1)
        res = find_best_move_guardian((3, 5), (2, 1), self.grid_map, self.weights)
        self.assertIn('best_move', res)
        self.assertIsNotNone(res['best_move'])
        self.assertGreater(res['nodes_visited'], 0)

    def test_intruder_behavior(self):
        # Intruder should select a valid move that keeps distance from guardian
        move = find_best_move_intruder((3, 5), (2, 1), self.grid_map)
        self.assertIsNotNone(move)
        # Should be adjacent to (2, 1) and walkable
        self.assertTrue(abs(move[0] - 2) + abs(move[1] - 1) <= 1)

class TestGeminiFallback(unittest.TestCase):
    def test_fallback_message_mentions_local_mode_when_api_missing(self):
        with patch.object(backend_main, 'GEMINI_API_KEY', ''):
            response = backend_main.explain_inference_chain_with_gemini(['intruso_detectado'])
        self.assertIn('Modo Local', response)
        self.assertNotIn('API Gemini Limite/Error', response)

    def test_fallback_message_mentions_local_mode_when_api_returns_error(self):
        with patch.object(backend_main, 'GEMINI_API_KEY', 'fake-key'):
            with patch('backend.main.requests.post') as mock_post:
                mock_post.return_value.status_code = 429
                response = backend_main.explain_inference_chain_with_gemini(['quiebre_stock'])
        self.assertIn('Modo Local', response)
        self.assertIn('lógica local', response.lower())

class TestVisionSystem(unittest.TestCase):
    def setUp(self):
        self.vision = VisionSystem()
        self.grid_state = {
            'celdas': [
                {'x': 1, 'y': 1, 'val': 1},
                {'x': 2, 'y': 1, 'val': 0},
                {'x': 3, 'y': 1, 'val': 1},
                {'x': 1, 'y': 2, 'val': 0},
                {'x': 2, 'y': 2, 'val': 0},
                {'x': 3, 'y': 2, 'val': 0},
                {'x': 1, 'y': 3, 'val': 1},
                {'x': 2, 'y': 3, 'val': 0},
                {'x': 3, 'y': 3, 'val': 1},
            ],
            'guardian_pos': [2, 2],
            'intruder_pos': [1, 2],
            'intruder_conf': 0.85,
            'camaras': [{'id': 'camara_1', 'x': 2, 'y': 2, 'estado': 'activa'}]
        }

    def test_image_processing_pipeline(self):
        res = self.vision.get_cell_image_and_process(self.grid_state, 'camara_1')
        self.assertIn('original', res)
        self.assertIn('grayscale', res)
        self.assertIn('blur', res)
        self.assertIn('canny', res)
        self.assertIn('yolo_detect', res)
        
        # Verify base64 strings are generated
        self.assertTrue(len(res['original']) > 0)
        self.assertTrue(len(res['canny']) > 0)
        
        # Ethics check: 85% confidence must trigger manual confirmation
        self.assertTrue(res['manual_confirmation_required'])

if __name__ == '__main__':
    unittest.main()
