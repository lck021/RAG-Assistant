import { useState, useRef, type ReactNode } from "react";
import { askQuestion, uploadFile } from "../api.ts";

interface AlertProps {
  type: string;
  children: ReactNode;
  onClose: () => void;
}

function App() {
  // for input and output fields
  const [question, setQuestion] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [answer, setAnswer] = useState("");

  // for loading states
  const [askLoading, setAskLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);

  // for alert messages
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // function to reach ask endpoint
  async function handleAsk(event: React.SubmitEvent) {
    event.preventDefault();

    setError(null);
    setAskLoading(true);
    try {
      const data = await askQuestion(question);
      setAnswer(data.response);
      setQuestion("");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setAskLoading(false);
    }
  }

  // function to reach upload endpoint
  async function handleUpload(event: React.SubmitEvent) {
    event.preventDefault();
    if (!file) return;

    setError(null);
    setUploadLoading(true);
    try {
      await uploadFile(file);
      setSuccess(`${file} successfully uploaded`);
      setFile(null);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setUploadLoading(false);
    }

    fileInputRef.current!.value = "";
  }

  return (
    <main className="container py-5" style={{ maxWidth: 720 }}>
      {/* title */}
      <header className="text-center mb-4">
        <h1 className="display-6 fw-bold">RAG Assistant</h1>
        <p className="text-muted mb-0">Ask a question about your documents.</p>
      </header>

      {/* danger alert message */}
      {error !== null && (
        <DangerAlert type="danger" onClose={() => setError(null)}>
          <strong>Error</strong> {error}
        </DangerAlert>
      )}

      {/* success alert message */}
      {success !== null && (
        <SuccessAlert type="success" onClose={() => setSuccess(null)}>
          <strong>Success!</strong> {success}
        </SuccessAlert>
      )}

      {/* main question card */}
      <div className="card shadow-sm mb-4">
        <div className="card-body">
          <form onSubmit={handleAsk}>
            <div className="input-group">
              <input
                type="text"
                value={question}
                className="form-control form-control-lg me-2 rounded"
                onChange={(event) => setQuestion(event.target.value)}
                maxLength={500}
                placeholder="Ask a question..."
              ></input>
              <button
                className="btn btn-primary btn-primary-lg rounded"
                type="submit"
                disabled={askLoading || !question.trim()}
              >
                {askLoading && (
                  <span className="spinner-border spinner-border-sm me-2" />
                )}
                {askLoading ? "Thinking…" : "Ask"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* answer card */}
      {answer && (
        <div className="card shadow-sm">
          <div className="card-header fw-semibold">Answer</div>
          <div className="card-body">
            <p className="card-text mb-0" style={{ whiteSpace: "pre-wrap" }}>
              {answer}
            </p>
          </div>
        </div>
      )}

      {/* input to upload files */}
      <div className="card shadow-sm mb-4">
        <div className="card-body">
          <h2 className="h5 mb-3">Upload a document</h2>
          <form onSubmit={handleUpload}>
            <div className="input-group">
              <input
                type="file"
                className="form-control form-control-lg me-2 rounded"
                accept=".txt"
                ref={fileInputRef}
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              ></input>
              <button
                className="btn btn-primary btn-primary-lg rounded"
                type="submit"
                disabled={uploadLoading || !file}
              >
                {uploadLoading && (
                  <span className="spinner-border spinner-border-sm me-2" />
                )}
                {uploadLoading ? "Uploading..." : "Upload"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}

function DangerAlert({ type, children, onClose }: AlertProps) {
  return (
    <div
      className={`alert alert-${type} alert-dismissible fade show`}
      role="alert"
    >
      {children}
      <button
        type="button"
        className="btn-close"
        onClick={onClose}
        aria-label="Close"
      ></button>
    </div>
  );
}

function SuccessAlert({ type, children, onClose }: AlertProps) {
  return (
    <div
      className={`alert alert-${type} alert-dismissible fade show`}
      role="alert"
    >
      {children}
      <button
        type="button"
        className="btn-close"
        onClick={onClose}
        aria-label="Close"
      ></button>
    </div>
  );
}

export default App;
