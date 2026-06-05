import google.generativeai as genai
import traceback

def test():
    try:
        genai.configure(api_key="AIzaSyD4i1mQjc6n-GlrWDeSmbe3_Dtcce4f-3A")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test()
