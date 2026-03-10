import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Workflow */}
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-lg font-semibold">Workflow Builder</h2>
          <p className="text-gray-600 mb-4">
            Build ETL pipelines and backend services visually.
          </p>
          <Link
            href="/workflow"
            className="inline-block bg-blue-600 text-white px-4 py-2 rounded"
          >
            Open Workflow
          </Link>
        </div>

        {/* AI */}
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-lg font-semibold">AI Assistant</h2>
          <p className="text-gray-600 mb-4">
            Generate workflows using natural language.
          </p>
          <Link
            href="/ai"
            className="inline-block bg-purple-600 text-white px-4 py-2 rounded"
          >
            Open AI Assistant
          </Link>
        </div>

        {/* Patients */}
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-lg font-semibold">Patients</h2>
          <p className="text-gray-600 mb-4">
            Manage patient records and clinical data.
          </p>
          <Link
            href="/patients"
            className="inline-block bg-green-600 text-white px-4 py-2 rounded"
          >
            View Patients
          </Link>
        </div>

        {/* Jobs */}
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-lg font-semibold">Job Dashboard</h2>
          <p className="text-gray-600 mb-4">
            Monitor workflow execution and view logs.
          </p>
          <Link
            href="/jobs"
            className="inline-block bg-orange-600 text-white px-4 py-2 rounded"
          >
            View Jobs
          </Link>
        </div>
      </div>
    </div>
  );
}

