"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, FileText, CheckCircle, AlertCircle } from "lucide-react"
import { useGenerateXml } from "@/hooks/use-files"
import { toast } from "@/components/ui/use-toast"
import type { FileModel, ItemDto } from "@/types/api"

interface ArticleSelectionProps {
  file: FileModel
  onBack: () => void
  onSuccess: () => void
}

export function ArticleSelection({ file, onBack, onSuccess }: ArticleSelectionProps) {
  const [selectedItems, setSelectedItems] = useState<Record<string, boolean>>({})
  const generateXmlMutation = useGenerateXml()

  // Initialize selected items based on confidence scores
  useEffect(() => {
    const initialSelected: Record<string, boolean> = {}
    file.items.forEach((item) => {
      initialSelected[item.commission] = item.confidence >= 0.9
    })
    setSelectedItems(initialSelected)
  }, [file.items])

  const handleItemToggle = (sku: string) => {
    setSelectedItems((prev) => ({
      ...prev,
      [sku]: !prev[sku],
    }))
  }


  const handleGenerateXml = async () => {
    try {
      const selectedIds = Object.keys(selectedItems).filter((key) => selectedItems[key])
      if (selectedIds.length === 0) {
        toast({
          title: "No items selected",
          description: "Please select at least one item to generate XML.",
          variant: "destructive",
        })
        return
      }
  
      await generateXmlMutation.mutateAsync({
        fileId: file.id,
        itemIds: selectedIds,
      })
  
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

  // Count selected items
  const selectedCount = Object.values(selectedItems).filter(Boolean).length
 
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
                <span className="block text-sm mt-2 font-medium">
                  {selectedCount} of {file.items.length} articles selected
                </span>
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
              {/* deselect everythib or select everythin buttin */}
              <div className="flex items-center space-x-2 mb-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedItems((prev) => ({ ...prev, ...Object.fromEntries(highConfidenceItems.map(item => [item.commission, true])) }))}
                >
                  Select All
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedItems((prev) => ({ ...prev, ...Object.fromEntries(highConfidenceItems.map(item => [item.commission, false])) }))}
                >
                  Deselect All
                </Button>
              </div>
              <div className="space-y-3">
                {highConfidenceItems.map((item, index) => (
                  <ArticleItem
                    key={index}
                    item={item}
                    isSelected={!!selectedItems[item.commission]}
                    onToggle={() => handleItemToggle(item.commission)}
                    isHighConfidence={true}
                  />
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
                {lowConfidenceItems.map((item, index) => (
                  <ArticleItem
                    key={index}
                    item={item}
                    isSelected={!!selectedItems[item.commission]}
                    onToggle={() => handleItemToggle(item.commission)}
                    isHighConfidence={false}
                  />
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
          <Button onClick={handleGenerateXml} disabled={selectedCount === 0 || generateXmlMutation.isPending}>
            {generateXmlMutation.isPending ? "Generating..." : `Generate XML (${selectedCount})`}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

// Separate component for each article item to prevent re-rendering issues
interface ArticleItemProps {
  item: ItemDto
  isSelected: boolean
  onToggle: () => void
  isHighConfidence: boolean
}

function ArticleItem({ item, isSelected, onToggle, isHighConfidence }: ArticleItemProps) {
  return (
    <div
      className={`flex items-start space-x-3 p-3 rounded-md border ${
        !isHighConfidence ? "border-amber-100 bg-amber-50" : ""
      }`}
    >
      <Checkbox id={`item-${item.commission}`} checked={isSelected} onCheckedChange={onToggle} />
      <div className="grid gap-1.5 leading-none">
        <label
          htmlFor={`item-${item.commission}`}
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
          <span className={isHighConfidence ? "text-green-600" : "text-amber-600"}>
            Confidence: {(item.confidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  )
}
