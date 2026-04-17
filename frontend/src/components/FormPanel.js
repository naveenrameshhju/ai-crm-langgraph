const FormPanel = ({ formData }) => {
  return (
    <div className="form-card">
      <h2>📋 Log HCP Interaction</h2>

      {/* SECTION 1 */}
      <h4 className="section-title">Interaction Details</h4>

      <div className="grid">
        <div>
          <label>HCP Name</label>
          <input value={formData.hcp_name || ""} readOnly />
        </div>

        <div>
          <label>Interaction Type</label>
          <input value={formData.interaction_type || ""} readOnly />
        </div>

        <div>
          <label>Date</label>
          <input value={formData.date || ""} readOnly />
        </div>

        <div>
          <label>Time</label>
          <input value={formData.time || ""} readOnly />
        </div>
      </div>

      {/* SECTION 2 */}
      <h4 className="section-title">Participants</h4>

      <div>
        <label>Attendees</label>
        <input value={formData.attendees || ""} readOnly />
      </div>

      {/* SECTION 3 */}
      <h4 className="section-title">Discussion</h4>

      <div>
        <label>Topics Discussed</label>
        <textarea value={formData.topics || ""} readOnly />
      </div>

      {/* SECTION 4 */}
      <h4 className="section-title">Materials</h4>

      <div>
        <label>Materials Shared</label>
        <input value={formData.materials || ""} readOnly />
      </div>

      {/* NOTES */}
      <div>
        <label>Notes</label>
        <textarea value={formData.notes || ""} readOnly />
      </div>
    </div>
  );
};

export default FormPanel;