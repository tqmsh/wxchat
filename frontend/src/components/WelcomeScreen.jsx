import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { CustomSelect } from "@/components/ui/custom-select"
import { ChatForm } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { transcribeAudio } from "@/lib/utils/audio"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"

export function WelcomeScreen({
  selectedModel,
  setSelectedModel,
  modelOptions,
  selectedBaseModel,
  setSelectedBaseModel,
  baseModelOptions,
  selectedRagModel,
  setSelectedRagModel,
  ragModelOptions,
  selectedHeavyModel,
  setSelectedHeavyModel,
  heavyModelOptions,
  useAgents,
  setUseAgents,
  append,
  handleSubmit,
  input,
  handleInputChange,
  isLoading,
  isTyping,
  stop,
  showReasoning,
  setShowReasoning
}) {
  const navigate = useNavigate()
  
  const handleLogout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8 relative">
      <Button
        onClick={handleLogout}
        variant="outline"
        size="sm"
        className="absolute top-4 right-4 text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700"
      >
        Logout
      </Button>
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">
          Welcome to GeoAnalysis Assistant.
        </h1>
        <p className="text-gray-600">
          Ask me anything about geospatial data analysis!
        </p>
        <div className="mt-4 flex flex-col items-center space-y-4">
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Mode</label>
            <CustomSelect
              value={selectedModel}
              onChange={setSelectedModel}
              options={modelOptions}
              placeholder="Select mode"
            />
          </div>
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Foundation Model</label>
            <CustomSelect
              value={selectedBaseModel}
              onChange={setSelectedBaseModel}
              options={baseModelOptions}
              placeholder="Foundation model"
            />
          </div>
          {selectedModel === "rag" && (
            <>
              <div className="w-48">
                <label className="block text-sm font-medium text-gray-700 mb-1">Embedding Model</label>
                <CustomSelect
                  value={selectedRagModel}
                  onChange={setSelectedRagModel}
                  options={ragModelOptions}
                  placeholder="Embedding model"
                />
              </div>
              <div className="w-48">
                <label className="block text-sm font-medium text-gray-700 mb-1">Heavy Reasoning Model</label>
                <CustomSelect
                  value={selectedHeavyModel}
                  onChange={setSelectedHeavyModel}
                  options={heavyModelOptions}
                  placeholder="Heavy reasoning model"
                />
              </div>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  className="form-checkbox h-4 w-4 text-blue-600"
                  checked={useAgents}
                  onChange={(e) => setUseAgents(e.target.checked)}
                />
                <span className="text-sm text-gray-700">Enable multi-agent debate</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  className="form-checkbox h-4 w-4 text-blue-600"
                  checked={showReasoning}
                  onChange={(e) => setShowReasoning(e.target.checked)}
                />
                <span className="text-sm text-gray-700">Show reasoning</span>
              </label>
            </>
          )}
        </div>
      </div>
      <PromptSuggestions
        label="Get started with some examples"
        append={append}
        suggestions={[
          "How do I analyze spatial patterns in demographic data?",
          "What GIS techniques can I use for environmental impact assessment?",
          "Can you help me interpret satellite imagery for land use classification?"
        ]}
      />
      <div className="w-full max-w-2xl pt-5">
        <ChatForm
          isPending={isLoading || isTyping}
          handleSubmit={handleSubmit}
        >
          {({ files, setFiles }) => (
            <MessageInput
              value={input}
              onChange={handleInputChange}
              allowAttachments
              files={files}
              setFiles={setFiles}
              stop={stop}
              isGenerating={false}
              transcribeAudio={transcribeAudio}
              placeholder="Ask me about geospatial analysis..."
            />
          )}
        </ChatForm>
      </div>
    </div>
  )
} 