import unittest
from unittest.mock import patch, MagicMock
from src.dataFetch import fetch_data_from_api, fetch_data_from_file

class TestDataFetch(unittest.TestCase):
    @patch('src.dataFetch.requests.get')
    def test_fetch_data_from_api_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response

        url = "http://example.com/api"
        result = fetch_data_from_api(url)
        self.assertEqual(result, {'key': 'value'})
        mock_get.assert_called_once_with(url)

    @patch('src.dataFetch.requests.get')
    def test_fetch_data_from_api_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = "http://example.com/api"
        result = fetch_data_from_api(url)
        self.assertIsNone(result)

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"foo": "bar"}')
    def test_fetch_data_from_file_success(self, mock_open):
        file_path = "dummy.json"
        result = fetch_data_from_file(file_path)
        self.assertEqual(result, {"foo": "bar"})
        mock_open.assert_called_once_with(file_path, 'r')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_fetch_data_from_file_not_found(self, mock_open):
        file_path = "notfound.json"
        result = fetch_data_from_file(file_path)
        self.assertIsNone(result)

    @patch('src.dataFetch.os.path.exists')
    @patch('src.dataFetch.pd.read_csv')
    def test_fetch_data_from_cached_csv_success(self, mock_read_csv, mock_exists):
        # Simulate that the cache file exists
        mock_exists.return_value = True
        mock_df = MagicMock()
        mock_read_csv.return_value = mock_df

        cache_path = "cache.csv"
        # Assuming fetch_data_from_file can load from CSV if file ends with .csv
        result = fetch_data_from_file(cache_path)
        mock_exists.assert_called_once_with(cache_path)
        mock_read_csv.assert_called_once_with(cache_path)
        self.assertEqual(result, mock_df)

    @patch('src.dataFetch.os.path.exists')
    def test_fetch_data_from_cached_csv_not_found(self, mock_exists):
        # Simulate that the cache file does not exist
        mock_exists.return_value = False
        cache_path = "missing_cache.csv"
        result = fetch_data_from_file(cache_path)
        mock_exists.assert_called_once_with(cache_path)
        self.assertIsNone(result)

    @patch('src.dataFetch.requests.get', side_effect=Exception("Network error"))
    def test_fetch_data_from_api_exception(self, mock_get):
        url = "http://example.com/api"
        result = fetch_data_from_api(url)
        self.assertIsNone(result)

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='not a json')
    def test_fetch_data_from_file_invalid_json(self, mock_open):
        file_path = "invalid.json"
        result = fetch_data_from_file(file_path)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()