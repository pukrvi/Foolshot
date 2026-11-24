import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from foolshot.market_nse_archive import archive_url, parse_fo, parse_indices

FO_HEADER = (
    "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,"
    "XpryDt,FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,"
    "LwPric,ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,"
    "ChngInOpnIntrst,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,"
    "Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4"
)
FO_ROWS = (
    "2026-11-20,2026-11-20,FO,NSE,IDO,9001,,NIFTY,,2026-11-26,2026-11-26,25000.00,"
    "CE,NIFTY26NOV25000CE,100.00,125.00,90.00,110.00,109.50,105.00,25100.25,112.00,"
    "4567,89,1234,45678900,42,F1,75,,,,,\n"
    "2026-11-20,2026-11-20,FO,NSE,IDF,9002,,NIFTY,,2026-11-26,2026-11-26,,,"
    "NIFTY26NOVFUT,25200.00,25300.00,25100.00,25250.00,25255.00,25100.00,25100.25,"
    "25260.00,12000,500,8000,201000000,900,F1,75,,,,,\n"
)
INDEX_CSV = (
    "Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,"
    "Closing Index Value,Points Change,Change(%),Volume,Turnover (Rs. Cr.),P/E,P/B,Div Yield\n"
    "Nifty 50,20-11-2026,25368,25808.8,25345.2,25800.6,286.3,1.12,428344270,42565.93,21.02,3.17,1.32\n"
    "Nifty50 Dividend Points,20-11-2026,-,-,-,216.43,0.0,-,-,-,-,-,-\n"
)


def _zip(csv_text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("BhavCopy_NSE_FO_0_0_0_20261120_F_0000.csv", csv_text)
    return buffer.getvalue()


class NseArchiveTests(unittest.TestCase):
    def test_archive_urls_use_compact_session_dates(self):
        self.assertEqual(
            archive_url("fo", "2026-11-20"),
            "https://nsearchives.nseindia.com/content/fo/"
            "BhavCopy_NSE_FO_0_0_0_20261120_F_0000.csv.zip",
        )
        self.assertEqual(
            archive_url("indices", "2023-11-23"),
            "https://nsearchives.nseindia.com/content/indices/ind_close_all_23112023.csv",
        )

    def test_fo_zip_is_parsed_from_a_suffixless_raw_blob(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "hash-named-blob"
            raw.write_bytes(_zip(FO_HEADER + "\n" + FO_ROWS))
            rows = parse_fo(raw)

        self.assertEqual(len(rows), 2)
        option, future = rows
        self.assertEqual(option["key"], "9001|2026-11-20")
        self.assertEqual(option["symbol"], "NIFTY")
        self.assertIsNone(option["available_at"])
        self.assertEqual(option["availability"], "unknown")
        self.assertEqual(option["values"]["option_type"], "CE")
        self.assertEqual(option["values"]["strike"], 25000.0)
        self.assertEqual(option["values"]["contract_name"], "NIFTY26NOV25000CE")
        self.assertEqual(option["values"]["instrument_type"], "IDO")
        self.assertEqual(option["values"]["underlying_price"], 25100.25)
        self.assertEqual(option["values"]["lot_size"], 75.0)
        self.assertEqual(option["values"]["turnover_rupees"], 45678900.0)
        self.assertEqual(future["values"]["instrument_type"], "IDF")
        self.assertNotIn("option_type", future["values"])

    def test_fo_archive_without_reviewed_columns_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "bad"
            raw.write_bytes(_zip("TradDt,TckrSymb\n2026-11-20,NIFTY\n"))
            with self.assertRaisesRegex(ValueError, "not the reviewed UDiFF"):
                parse_fo(raw)

    def test_index_close_file_allows_point_only_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "indices"
            raw.write_bytes(INDEX_CSV.encode())
            rows = parse_indices(raw)

        self.assertEqual(len(rows), 2)
        nifty, dividend = rows
        self.assertEqual(nifty["key"], "NSE_INDEX|Nifty 50|2026-11-20")
        self.assertEqual(nifty["values"]["close"], 25800.6)
        self.assertEqual(nifty["values"]["turnover_crore"], 42565.93)
        self.assertEqual(dividend["values"]["close"], 216.43)
        self.assertNotIn("open", dividend["values"])


if __name__ == "__main__":
    unittest.main()
