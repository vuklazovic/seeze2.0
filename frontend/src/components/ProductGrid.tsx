import { useState } from "react";
import { Filter, Grid, List, SlidersHorizontal, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Import product images
import headphonesImg from "@/assets/headphones.jpg";
import laptopImg from "@/assets/laptop.jpg";
import smartphoneImg from "@/assets/smartphone.jpg";
import mugImg from "@/assets/mug.jpg";

interface Product {
  id: number;
  name: string;
  price: number;
  rating: number;
  reviews: number;
  image: string;
  category: string;
  badge?: string;
}

const products: Product[] = [
  {
    id: 1,
    name: "Premium Wireless Headphones",
    price: 299.99,
    rating: 4.8,
    reviews: 256,
    image: headphonesImg,
    category: "Electronics",
    badge: "Best Seller",
  },
  {
    id: 2,
    name: "Ultra-Slim Laptop Pro",
    price: 1299.99,
    rating: 4.9,
    reviews: 189,
    image: laptopImg,
    category: "Electronics",
  },
  {
    id: 3,
    name: "Smart Phone X1",
    price: 899.99,
    rating: 4.7,
    reviews: 342,
    image: smartphoneImg,
    category: "Electronics",
    badge: "New",
  },
  {
    id: 4,
    name: "Minimalist Coffee Mug",
    price: 24.99,
    rating: 4.6,
    reviews: 128,
    image: mugImg,
    category: "Home",
  },
  {
    id: 5,
    name: "Premium Wireless Headphones Pro",
    price: 399.99,
    rating: 4.9,
    reviews: 445,
    image: headphonesImg,
    category: "Electronics",
    badge: "Premium",
  },
  {
    id: 6,
    name: "Gaming Laptop Elite",
    price: 1799.99,
    rating: 4.8,
    reviews: 267,
    image: laptopImg,
    category: "Electronics",
  },
];

export const ProductGrid = () => {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [sortBy, setSortBy] = useState("featured");

  return (
    <div className="flex-1 p-6">
      {/* Controls */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-foreground">Products</h1>
          <span className="text-muted-foreground">({products.length} items)</span>
        </div>

        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm">
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Filters
          </Button>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="featured">Featured</SelectItem>
              <SelectItem value="price-low">Price: Low to High</SelectItem>
              <SelectItem value="price-high">Price: High to Low</SelectItem>
              <SelectItem value="rating">Highest Rated</SelectItem>
              <SelectItem value="newest">Newest</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex items-center border border-border rounded-md">
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("grid")}
              className="rounded-r-none"
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("list")}
              className="rounded-l-none"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Product Grid */}
      <div className={`grid ${
        viewMode === "grid" 
          ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" 
          : "grid-cols-1 gap-4"
      }`}>
        {products.map((product) => (
          <Card
            key={product.id}
            className="overflow-hidden hover:shadow-hover transition-all duration-300 cursor-pointer group"
          >
            <div className="relative">
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
              />
              {product.badge && (
                <span className="absolute top-2 left-2 bg-primary text-primary-foreground text-xs px-2 py-1 rounded-md">
                  {product.badge}
                </span>
              )}
            </div>
            
            <div className="p-4">
              <h3 className="font-semibold text-foreground mb-2 line-clamp-2">
                {product.name}
              </h3>
              
              <div className="flex items-center space-x-1 mb-2">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`h-3 w-3 ${
                        i < Math.floor(product.rating)
                          ? "fill-yellow-400 text-yellow-400"
                          : "text-gray-300"
                      }`}
                    />
                  ))}
                </div>
                <span className="text-sm text-muted-foreground">
                  {product.rating} ({product.reviews})
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold text-foreground">
                  ${product.price}
                </span>
                <Button size="sm" className="bg-gradient-brand hover:opacity-90">
                  Add to Cart
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};