
    $(document).ready(function () {
        $('#submit-vote').on('click', function (e) {
                
                e.preventDefault(); // Prevent the default form submission

                // Get the selected candidate's ID
                var selectedCandidateId = $('input[name="vote"]:checked').val();

                // Send an AJAX request
                $.ajax({
                    url: "{{ url_for('voter') }}",
                    method: "POST",
                    data: { vote: selectedCandidateId },
                    success: function (response) {
                        // Handle the success response if needed
                        console.log('Vote submitted successfully');
                    },
                    error: function (xhr, status, error) {
                        // Handle errors if the AJAX request fails
                        console.error('Error submitting vote:', error);
                    }
                });
            });
        });
