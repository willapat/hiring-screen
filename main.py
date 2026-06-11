import pyperclip
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from tools.file_tools import read_resume
from agents.supervisor import run

load_dotenv()


def get_job_description() -> str:
    print("Copy the full job description text (Cmd+A, Cmd+C on the page), then press Enter:")
    input()
    return pyperclip.paste().strip()


def main():
    llm = init_chat_model("gemini-3.1-flash-lite", model_provider="google_genai", temperature=0)

    resume_path = input("Path to your resume (.pdf or .txt): ").strip()
    resume_text = read_resume(resume_path)

    while True:
        job_description = get_job_description()
        print("\nAnalyzing fit...\n")
        try:
            result = run(llm, job_description, resume_text)
            print(result)
            break
        except ValueError as e:
            print(f"\n{e}\n")


if __name__ == "__main__":
    main()
