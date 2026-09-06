from backend.services.rag import load_vectorstore


def main() -> None:
    load_vectorstore()
    print("Vector store ready.")


if __name__ == "__main__":
    main()

