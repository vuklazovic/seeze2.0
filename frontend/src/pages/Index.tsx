import { ShoppingHeader } from "@/components/ShoppingHeader";
import { SavedQueries } from "@/components/SavedQueries";
import { ProductGrid } from "@/components/ProductGrid";
import { ChatAssistant } from "@/components/ChatAssistant";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-subtle">
      <ShoppingHeader />
      <div className="flex h-[calc(100vh-80px)]">
        <SavedQueries />
        <ProductGrid />
        <ChatAssistant />
      </div>
    </div>
  );
};

export default Index;
