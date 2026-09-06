export default function AssetInventory() {
  return (
    <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
      <h2 className="text-base font-semibold text-[var(--foreground)] mb-6">Asset Inventory Preview</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[var(--muted-foreground)] border-b border-[var(--border)]">
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
              <td colSpan={6} className="py-12 text-center text-[var(--muted-foreground)]">
                No assets discovered.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
