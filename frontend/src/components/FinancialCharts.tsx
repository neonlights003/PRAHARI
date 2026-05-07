import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card } from './ui/Card'
import { DollarSign } from 'lucide-react'
import { formatIndianCurrency } from '@/lib/currency'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658']

interface FinancialChartsProps {
  data: any
}

export function FinancialCharts({ data }: FinancialChartsProps) {
  const financialAnalysis = data?.financialAnalysis

  if (!financialAnalysis) {
    return null
  }

  const bidAmount = financialAnalysis.bidAmount
  const pricingStructure = financialAnalysis.pricingStructure
  const financialHealth = financialAnalysis.financialHealth
  const itemizedCosts = pricingStructure?.itemizedCostBreakdown || []

  const safeNumber = (val: any): number => {
    const num = Number(val)
    return isNaN(num) ? 0 : num
  }

  // Build bid amount breakdown data for pie chart
  const bidAmountData = []
  if (bidAmount?.basePrice) {
    const value = safeNumber(bidAmount.basePrice)
    if (value > 0) bidAmountData.push({ name: 'Base Price', value })
  }
  if (bidAmount?.taxesAndDuties) {
    const value = safeNumber(bidAmount.taxesAndDuties)
    if (value > 0) bidAmountData.push({ name: 'Taxes & Duties', value })
  }

  // Build itemized cost breakdown data for bar chart
  const costBreakdownData = itemizedCosts
    .filter((item: any) => safeNumber(item.totalCost) > 0 && item.itemDescription)
    .map((item: any) => ({
      name: item.itemDescription?.length > 20 ? item.itemDescription.substring(0, 20) + '...' : item.itemDescription,
      fullName: item.itemDescription,
      value: safeNumber(item.totalCost),
      unitPrice: safeNumber(item.unitPrice),
      quantity: safeNumber(item.quantity)
    }))

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * Math.PI / 180)
    const y = cy + radius * Math.sin(-midAngle * Math.PI / 180)

    if (percent < 0.05) return null

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs font-semibold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length && payload[0]?.value !== undefined) {
      const value = safeNumber(payload[0].value)
      const item = payload[0].payload
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded shadow-lg">
          <p className="font-semibold text-sm text-gray-900 dark:text-gray-100">{item.fullName || payload[0].name}</p>
          <p className="text-primary font-bold">{formatIndianCurrency(value)}</p>
          {item.unitPrice !== undefined && item.quantity !== undefined && (
            <p className="text-xs text-muted-foreground">
              Unit: {formatIndianCurrency(item.unitPrice)} × {item.quantity}
            </p>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-4">
      {/* Bid Amount Summary Cards */}
      {bidAmount && (
        <div className="grid md:grid-cols-3 gap-4">
          {bidAmount.totalBidValue && (
            <Card className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950">
              <div className="text-sm text-muted-foreground mb-1">Total Bid Value</div>
              <div className="text-xl font-bold text-primary">
                {formatIndianCurrency(safeNumber(bidAmount.totalBidValue))}
              </div>
            </Card>
          )}
          {bidAmount.basePrice && (
            <Card className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950">
              <div className="text-sm text-muted-foreground mb-1">Base Price</div>
              <div className="text-xl font-bold text-green-600">
                {formatIndianCurrency(safeNumber(bidAmount.basePrice))}
              </div>
            </Card>
          )}
          {bidAmount.totalPriceWithTax && (
            <Card className="p-3 bg-gradient-to-r from-purple-50 to-violet-50 dark:from-purple-950 dark:to-violet-950">
              <div className="text-sm text-muted-foreground mb-1">Total with Tax</div>
              <div className="text-xl font-bold text-purple-600">
                {formatIndianCurrency(safeNumber(bidAmount.totalPriceWithTax))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Itemized Cost Breakdown Table */}
      {costBreakdownData.length > 0 && (
        <Card className="p-4">
          <h4 className="text-base font-semibold mb-3 flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-indigo-600" />
            Itemized Cost Breakdown
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-indigo-200 dark:border-indigo-800">
                  <th className="text-left py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Item Description</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Unit Price</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Quantity</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Total Cost</th>
                </tr>
              </thead>
              <tbody>
                {costBreakdownData.map((item: any, index: number) => (
                  <tr key={index} className="border-b border-gray-100 dark:border-gray-800 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/50 transition-colors">
                    <td className="py-3 px-2">
                      <span className="font-medium text-gray-800 dark:text-gray-200">{item.fullName}</span>
                    </td>
                    <td className="text-right py-3 px-2 text-gray-600 dark:text-gray-400">
                      {item.unitPrice > 0 ? formatIndianCurrency(item.unitPrice) : '—'}
                    </td>
                    <td className="text-right py-3 px-2 text-gray-600 dark:text-gray-400">
                      {item.quantity > 0 ? item.quantity : '—'}
                    </td>
                    <td className="text-right py-3 px-2 font-semibold text-gray-900 dark:text-gray-100">
                      {formatIndianCurrency(item.value)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950">
                  <td colSpan={3} className="py-3 px-2 font-bold text-gray-800 dark:text-gray-200">Total</td>
                  <td className="text-right py-3 px-2 font-bold text-gray-900 dark:text-gray-100">
                    {formatIndianCurrency(costBreakdownData.reduce((sum: number, item: any) => sum + item.value, 0))}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </Card>
      )}

      {/* Bid Amount Pie Chart */}
      {bidAmountData.length > 1 && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="p-4">
            <h4 className="text-base font-semibold mb-3 text-center">Bid Amount Breakdown</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={bidAmountData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomLabel}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {bidAmountData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  layout="horizontal"
                  verticalAlign="bottom"
                  align="center"
                  wrapperStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          {/* Financial Health Card */}
          {financialHealth && (
            <Card className="p-4">
              <h4 className="text-base font-semibold mb-3 text-center">Bidder Financial Health</h4>
              <div className="space-y-3.5">
                {financialHealth.annualTurnover && (
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                    <span className="text-sm text-muted-foreground">Annual Turnover</span>
                    <span className="text-base font-semibold">{financialHealth.annualTurnover}</span>
                  </div>
                )}
                {financialHealth.netWorth && (
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                    <span className="text-sm text-muted-foreground">Net Worth</span>
                    <span className="text-base font-semibold">{financialHealth.netWorth}</span>
                  </div>
                )}
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                  <span className="text-sm text-muted-foreground">Solvency Certificate</span>
                  <span className={`text-base font-semibold ${financialHealth.solvencyCertificate ? 'text-green-600' : 'text-red-600'}`}>
                    {financialHealth.solvencyCertificate ? 'Provided' : 'Not Provided'}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                  <span className="text-sm text-muted-foreground">Audited Financials</span>
                  <span className={`text-base font-semibold ${financialHealth.auditedFinancialsProvided ? 'text-green-600' : 'text-red-600'}`}>
                    {financialHealth.auditedFinancialsProvided ? 'Provided' : 'Not Provided'}
                  </span>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Cost Comparison Bar Chart */}
      {costBreakdownData.length > 0 && (
        <Card className="p-4">
          <h4 className="text-base font-semibold mb-3">Cost Components Comparison</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={costBreakdownData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={100}
                style={{ fontSize: '11px' }}
              />
              <YAxis
                tickFormatter={(value) => `₹${(value / 100000).toFixed(1)}L`}
                label={{ value: 'Amount (Lakhs)', angle: -90, position: 'insideLeft', style: { fontSize: '12px' } }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" fill="#0EA5E9" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Payment Terms */}
      {pricingStructure?.paymentTerms && (
        <Card className="p-4">
          <h4 className="text-base font-semibold mb-2">Payment Terms</h4>
          <p className="text-base text-muted-foreground">{pricingStructure.paymentTerms}</p>
        </Card>
      )}
    </div>
  )
}
