import { useState } from "react";
import { Send, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Message {
  id: number;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

const initialMessages: Message[] = [
  {
    id: 1,
    content: "Hello! I'm your shopping assistant. How can I help you find the perfect product today?",
    isBot: true,
    timestamp: new Date(),
  },
];

export const ChatAssistant = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      content: inputValue,
      isBot: false,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    // Simulate bot response
    setTimeout(() => {
      const botResponse: Message = {
        id: messages.length + 2,
        content: "I understand you're looking for that. Let me help you find the best options based on your preferences and budget.",
        isBot: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    }, 1000);

    setInputValue("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  return (
    <div className="w-80 bg-muted/30 border-l border-border flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground flex items-center">
          <Bot className="h-5 w-5 mr-2" />
          Shopping Assistant
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Ask me anything about products
        </p>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isBot ? "justify-start" : "justify-end"}`}
            >
              <Card className={`max-w-[80%] p-3 ${
                message.isBot 
                  ? "bg-background" 
                  : "bg-primary text-primary-foreground"
              }`}>
                <div className="flex items-start space-x-2">
                  {message.isBot ? (
                    <Bot className="h-4 w-4 mt-1 flex-shrink-0" />
                  ) : (
                    <User className="h-4 w-4 mt-1 flex-shrink-0" />
                  )}
                  <p className="text-sm leading-relaxed">{message.content}</p>
                </div>
              </Card>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border">
        <div className="flex space-x-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about products..."
            className="flex-1"
          />
          <Button onClick={handleSendMessage} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};