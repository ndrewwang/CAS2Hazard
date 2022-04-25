# CAS2Hazard

This Python project takes a list of CAS numbers for the chemicals in your inventory and scrapes Sigma-Aldrich website to retrieve a compilation of Hazard statements (e.g. H319), Precautionary statements (e.g. P120) and recommendations for Personal Protective Equipment. It outputs (4) CSV files.

Based on original code from: https://github.com/arnauddevie/Hazard-Assessment-CAS-Lookup

Webscraping sections that may break due to location specific or alterations to the Sigma-Aldrich website are marked with a `#@SigmaAldrich` tag in the commented code for `CAS2Hazard.py`.

Todo:
Output (1) folder with SDS PDF files downloaded (via Chromedriver)