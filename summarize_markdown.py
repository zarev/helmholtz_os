import argparse
import os
import google.generativeai as genai

def find_supported_model():
    """Finds a supported generative model."""
    try:
        # Ensure the API key is set
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)

        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Using model: {m.name}")
                return m.name
    except Exception as e:
        print(f"An error occurred while listing models: {e}")
        return None
    return None


def summarize_with_gemini(markdown_content, model_name):
    """
    Summarizes the given markdown content using the Gemini API.
    """
    if not model_name:
        return "Could not find a suitable model for summarization."
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"""Please summarize the following research paper, which is in markdown format. Provide a concise summary in plain text:

{markdown_content}"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred during summarization: {e}"

def summarize_markdown_to_text(markdown_file_path, output_file_path):
    """
    Reads a markdown file, summarizes it using the Gemini API,
    and writes the summary to a plain text file.
    """
    try:
        model_name = find_supported_model()
        if not model_name:
            print("Could not find a supported model. Aborting.")
            return

        with open(markdown_file_path, 'r', encoding='utf-8') as md_file:
            markdown_content = md_file.read()

        summary_text = summarize_with_gemini(markdown_content, model_name)

        with open(output_file_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(summary_text.strip())

        print(f"Successfully summarized '{markdown_file_path}' to '{output_file_path}' using Gemini.")

    except FileNotFoundError:
        print(f"Error: File not found at '{markdown_file_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize a markdown file into a plain text file using the Gemini API.")
    parser.add_argument("markdown_file", help="Path to the input markdown file.")
    parser.add_argument("output_file", help="Path to the output plain text file.")
    args = parser.parse_args()

    summarize_markdown_to_text(args.markdown_file, args.output_file)
