import React from 'react';
import '../style/Description.css';

class Description extends React.Component {
    constructor(props) {
        super(props)
    }

    render() {
        return (
            <div> 
                <h1>Zest Race Predictor</h1>
                <br />
                <div className="description">
                    <p> The <em>Zest Race Predictor (ZRP)</em> is an improved race prediction technology designed to <em>improve accountability</em> and <em>better facilitate fair lending</em>. This web application compares the ZRP with the current standard model used by the Consumer Financial Protection Bureau, BisG.
                    <br /><br />
                    By <em>Zest.Ai</em> and <em>Harvard Tech for Social Good</em></p>
                </div>
                <hr style={{
                    width: "50%"
                }}></hr>
            </div>
        )
    }
}


export default Description;