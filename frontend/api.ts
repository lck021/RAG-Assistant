export async function askQuestion(question: string) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: question }),
  });

  if (!response.ok) {
    if (response.status === 422)
      throw new Error(`Please enter a valid question.`);
    throw new Error(`${response.status}`);
  }

  return response.json();
}

export async function uploadFile(file: File) {
  let formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 422) {
      throw new Error("Incorrect file type");
    }
    throw new Error(`${response.status}`);
  }

  return response.json();
}
