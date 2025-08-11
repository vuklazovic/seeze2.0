import { Search, ShoppingBag, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const ShoppingHeader = () => {
  return (
    <header className="bg-background border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <h1 className="text-2xl font-bold text-foreground">ShopMart</h1>
          <nav className="hidden md:flex space-x-6">
            <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
              Electronics
            </Button>
            <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
              Fashion
            </Button>
            <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
              Home
            </Button>
            <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
              Books
            </Button>
          </nav>
        </div>

        <div className="flex-1 max-w-md mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search products..."
              className="pl-10 bg-muted/50 border-border focus:bg-background"
            />
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="icon">
            <User className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon" className="relative">
            <ShoppingBag className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center">
              2
            </span>
          </Button>
        </div>
      </div>
    </header>
  );
};