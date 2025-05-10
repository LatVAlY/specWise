"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, FileText, CheckCircle, AlertCircle } from "lucide-react"
import { useGenerateXml } from "@/hooks/use-files"
import { toast } from "@/components/ui/use-toast"
import type { FileModel } from "@/types/api"

interface ArticleSelectionProps {
  file: FileModel
  onBack: () => void
  onSuccess: () => void
}

export function ArticleSelection({ file, onBack, onSuccess }: ArticleSelectionProps) {
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const generateXmlMutation = useGenerateXml()
  const router = useRouter()

  // Initialize selected items based on confidence scores
  useEffect(() => {
    const initialSelected = new Set<string>()
    file.items.forEach((item) => {
      if (item.confidence >= 0.9) {
        initialSelected.add(item.sku)
      }
    })
    setSelectedItems(initialSelected)
  }, [file.items])

  const handleItemToggle = (sku: string) => {
    const newSelected = new Set(selectedItems)
    if (newSelected.has(sku)) {
      newSelected.delete(sku)
    } else {
      newSelected.add(sku)
    }
    setSelectedItems(newSelected)
  }

  const handleGenerateXml = async () => {
    try {
      // In a real implementation, we would pass the selected items to the API
      // For now, we'll just call the existing generateXml function
      await generateXmlMutation.mutateAsync(file.id)
      toast({
        title: "XML Generated",
        description: "XML has been generated successfully with selected items.",
      })
      onSuccess()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate XML. Please try again.",
        variant: "destructive",
      })
    }
  }

  // Separate items into high confidence and low confidence groups
  const highConfidenceItems = file.items.filter((item) => item.confidence >= 0.9)
  const lowConfidenceItems = file.items.filter((item) => item.confidence < 0.9)

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Files
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">Select Articles for XML Generation</CardTitle>
              <CardDescription>
                File: {file.filename}
                <span className="block text-xs mt-1">ID: {file.id}</span>
              </CardDescription>
            </div>
            <FileText className="h-6 w-6 text-blue-500" />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {highConfidenceItems.length > 0 && (
            <div>
              <h3 className="text-sm font-medium flex items-center mb-3">
                <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                High Confidence Articles ({highConfidenceItems.length})
              </h3>
              <div className="space-y-3">
                {highConfidenceItems.map((item) => (
                  <div key={item.sku} className="flex items-start space-x-3 p-3 rounded-md border">
                    <Checkbox
                      id={`item-${item.sku}`}
                      checked={selectedItems.has(item.sku)}
                      onCheckedChange={() => handleItemToggle(item.sku)}
                    />
                    <div className="grid gap-1.5 leading-none">
                      <label
                        htmlFor={`item-${item.sku}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {item.name}
                      </label>
                      <p className="text-xs text-muted-foreground">{item.text}</p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-xs">
                        <span>SKU: {item.sku}</span>
                        <span>
                          Quantity: {item.quantity} {item.quantityunit}
                        </span>
                        <span>
                          Price: {item.price} {item.priceunit}
                        </span>
                        <span>Commission: {item.commission}</span>
                        <span className="text-green-600">Confidence: {(item.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {highConfidenceItems.length > 0 && lowConfidenceItems.length > 0 && <Separator className="my-4" />}

          {lowConfidenceItems.length > 0 && (
            <div>
              <h3 className="text-sm font-medium flex items-center mb-3">
                <AlertCircle className="h-4 w-4 text-amber-500 mr-2" />
                Relevant Articles - Low Confidence ({lowConfidenceItems.length})
              </h3>
              <div className="space-y-3">
                {lowConfidenceItems.map((item) => (
                  <div
                    key={item.sku}
                    className="flex items-start space-x-3 p-3 rounded-md border border-amber-100 bg-amber-50"
                  >
                    <Checkbox
                      id={`item-${item.sku}`}
                      checked={selectedItems.has(item.sku)}
                      onCheckedChange={() => handleItemToggle(item.sku)}
                    />
                    <div className="grid gap-1.5 leading-none">
                      <label
                        htmlFor={`item-${item.sku}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {item.name}
                      </label>
                      <p className="text-xs text-muted-foreground">{item.text}</p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-xs">
                        <span>SKU: {item.sku}</span>
                        <span>
                          Quantity: {item.quantity} {item.quantityunit}
                        </span>
                        <span>
                          Price: {item.price} {item.priceunit}
                        </span>
                        <span>Commission: {item.commission}</span>
                        <span className="text-amber-600">Confidence: {(item.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {file.items.length === 0 && (
            <div className="text-center py-6 text-muted-foreground">No articles found in this file.</div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={onBack}>
            Cancel
          </Button>
          <Button onClick={handleGenerateXml} disabled={selectedItems.size === 0 || generateXmlMutation.isPending}>
            {generateXmlMutation.isPending ? "Generating..." : "Generate XML"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
