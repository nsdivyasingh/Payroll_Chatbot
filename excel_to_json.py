import pandas as pd
import json

file_name = 'FAQ_data.xlsx'

def convert_excel_to_json(input_file, output_file):
    try:
       
        all_sheets = pd.read_excel(input_file, sheet_name=None)
        
        all_faqs = []

        for sheet_name, df in all_sheets.items():
            print(f"Processing sheet: {sheet_name}...")
            
            current_q = str(df.columns[0]).strip()
            current_a = []

            for val in df.iloc[:, 0]:
                val_str = str(val).strip()
                
                if not val_str or val_str.lower() == 'nan':
                    continue
                
                if val_str.endswith('?'):
                    if current_q:
                        all_faqs.append({
                            "question": current_q, 
                            "answer": "\n".join(current_a).strip(),
                            "source": sheet_name
                        })
                    current_q = val_str
                    current_a = []
                else:
                    current_a.append(val_str)

            if current_q:
                all_faqs.append({
                    "question": current_q, 
                    "answer": "\n".join(current_a).strip(),
                    "source": sheet_name
                })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_faqs, f, indent=4, ensure_ascii=False)

        print(f"\nSuccess! Found {len(all_faqs)} total questions across all sheets.")
        print(f"File saved as: {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        print("Tip: Make sure you have the 'openpyxl' library: pip install openpyxl")

convert_excel_to_json(file_name, 'faq_all.json')