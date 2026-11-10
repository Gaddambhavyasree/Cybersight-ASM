export default function AssetInventory() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <h2 className="text-base font-semibold text-slate-100 mb-6">Asset Inventory Preview</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-800">
              <th className="pb-3 font-medium">Hostname</th>
              <th className="pb-3 font-medium">IP Address</th>
              <th className="pb-3 font-medium">Technology</th>
              <th className="pb-3 font-medium">Ports</th>
              <th className="pb-3 font-medium">Status</th>
              <th className="pb-3 font-medium">Risk</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={6} className="py-12 text-center text-slate-600">
                No assets discovered.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
