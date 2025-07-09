import unittest

# Define the test suite
suite = unittest.TestLoader().discover("tests")

# Run the test suite
if __name__ == "__main__":
    unittest.main(defaultTest="suite")
